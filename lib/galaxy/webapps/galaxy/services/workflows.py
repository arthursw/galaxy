import json
import logging
import os
import tempfile
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from galaxy import (
    exceptions,
    web,
)
from galaxy.managers.context import ProvidesUserContext
from galaxy.managers.workflows import (
    RefactorResponse,
    WorkflowContentsManager,
    WorkflowSerializer,
    WorkflowsManager,
)
from galaxy.model import StoredWorkflow
from galaxy.schema.invocation import WorkflowInvocationResponse
from galaxy.schema.schema import (
    InvocationsStateCounts,
    WorkflowIndexQueryPayload,
)
from galaxy.schema.workflows import (
    ExecuteWithWetlandsPayload,
    ExecuteWithWetlandsResponse,
    InvokeWorkflowPayload,
    StoredWorkflowDetailed,
)
from galaxy.util.tool_shed.tool_shed_registry import Registry
from galaxy.webapps.galaxy.services.base import ServiceBase
from galaxy.webapps.galaxy.services.notifications import NotificationService
from galaxy.webapps.galaxy.services.sharable import ShareableService
from galaxy.workflow.run import queue_invoke
from galaxy.workflow.run_request import build_workflow_run_configs

# Import the execute_workflow module
try:
    from execute_workflow import execute_workflow
except ImportError:
    # Fallback to looking in the Galaxy root directory
    import sys
    galaxy_root = Path(__file__).resolve().parents[5]
    sys.path.insert(0, str(galaxy_root))
    from execute_workflow import execute_workflow

log = logging.getLogger(__name__)


def convert_galaxy_inputs_to_wetlands_format(galaxy_inputs: Dict[str, Any], trans: ProvidesUserContext) -> Dict[str, Any]:
    """
    Convert Galaxy workflow inputs format to Wetlands format.
    
    Galaxy format:
    {
      "0": {
        "batch": false,
        "product": false,
        "values": [
          {"id": "dataset_id", "src": "hdca" | "hda", "map_over_type": null}
        ]
      }
    }
    
    Wetlands format:
    {
      "0": {
        "collection_type": "list",
        "elements": [
          {"identifier": "img_1", "path": "/path/to/file1.tif"},
          {"identifier": "img_2", "path": "/path/to/file2.tif"}
        ]
      }
    }
    
    Or for single datasets:
    {
      "1": {
        "path": "/path/to/file.txt"
      }
    }
    """
    converted_inputs = {}
    
    for step_id, input_spec in galaxy_inputs.items():
        if isinstance(input_spec, dict) and "values" in input_spec:
            values = input_spec["values"]
            
            if not values:
                continue
                
            # Check if this is a collection (hdca) or single datasets
            is_collection = any(v.get("src") == "hdca" for v in values)
            
            if is_collection and len(values) == 1:
                # Single collection input
                dataset_id = values[0].get("id")
                src = values[0].get("src")
                
                if src == "hdca":
                    # It's a dataset collection - we need to resolve it
                    try:
                        dataset_collection = trans.sa_session.query(
                            trans.app.model.DatasetCollection
                        ).filter_by(id=trans.security.decode_id(dataset_id)).first()
                        
                        if dataset_collection:
                            elements = []
                            for dce in dataset_collection.elements:
                                if dce.dataset:
                                    elements.append({
                                        "identifier": dce.element_index,
                                        "path": dce.dataset.get_file_name()
                                    })
                            
                            if elements:
                                converted_inputs[step_id] = {
                                    "collection_type": "list",
                                    "elements": elements
                                }
                    except Exception as e:
                        log.warning(f"Could not resolve dataset collection {dataset_id}: {e}")
                        
            elif not is_collection and len(values) == 1:
                # Single dataset input
                dataset_id = values[0].get("id")
                src = values[0].get("src")
                
                if src == "hda":
                    # It's a single dataset
                    try:
                        dataset = trans.sa_session.query(
                            trans.app.model.Dataset
                        ).filter_by(id=trans.security.decode_id(dataset_id)).first()
                        
                        if dataset:
                            converted_inputs[step_id] = {
                                "path": dataset.get_file_name()
                            }
                    except Exception as e:
                        log.warning(f"Could not resolve dataset {dataset_id}: {e}")
        else:
            # Pass through other input formats
            converted_inputs[step_id] = input_spec
    
    return converted_inputs


class WorkflowIndexPayload(WorkflowIndexQueryPayload):
    missing_tools: bool = False


class WorkflowsService(ServiceBase):
    def __init__(
        self,
        workflows_manager: WorkflowsManager,
        workflow_contents_manager: WorkflowContentsManager,
        serializer: WorkflowSerializer,
        tool_shed_registry: Registry,
        notification_service: NotificationService,
    ):
        self._workflows_manager = workflows_manager
        self._workflow_contents_manager = workflow_contents_manager
        self._serializer = serializer
        self.shareable_service = ShareableService(workflows_manager, serializer, notification_service)
        self._tool_shed_registry = tool_shed_registry

    def index(
        self,
        trans: ProvidesUserContext,
        payload: WorkflowIndexPayload,
        include_total_count: bool = False,
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        user = trans.user
        missing_tools = payload.missing_tools
        query, total_matches = self._workflows_manager.index_query(trans, payload, include_total_count)
        rval = []
        for wf in query.all():
            item = wf.to_dict(
                value_mapper={"id": trans.security.encode_id, "latest_workflow_id": trans.security.encode_id}
            )
            encoded_id = trans.security.encode_id(wf.id)
            item["annotations"] = [x.annotation for x in wf.annotations]
            item["url"] = web.url_for("workflow", id=encoded_id)
            item["owner"] = wf.user.username
            item["source_metadata"] = wf.latest_workflow.source_metadata
            if not payload.skip_step_counts:
                item["number_of_steps"] = wf.latest_workflow.step_count
            item["show_in_tool_panel"] = False
            if user is not None:
                item["show_in_tool_panel"] = wf.show_in_tool_panel(user_id=user.id)
            rval.append(item)
        if missing_tools:
            workflows_missing_tools = []
            workflows = []
            workflows_by_toolshed = {}
            for value in rval:
                stored_workflow = self._workflows_manager.get_stored_workflow(trans, value["id"], by_stored_id=True)
                tools = self._workflow_contents_manager.get_all_tools(stored_workflow.latest_workflow)
                missing_tool_ids = [
                    tool["tool_id"] for tool in tools if trans.app.toolbox.is_missing_shed_tool(tool["tool_id"])
                ]
                if len(missing_tool_ids) > 0:
                    value["missing_tools"] = missing_tool_ids
                    workflows_missing_tools.append(value)
            for workflow in workflows_missing_tools:
                for tool_id in workflow["missing_tools"]:
                    toolshed, _, owner, name, tool, version = tool_id.split("/")
                    shed_url = self.__get_full_shed_url(toolshed)
                    repo_identifier = "/".join((toolshed, owner, name))
                    if repo_identifier not in workflows_by_toolshed:
                        workflows_by_toolshed[repo_identifier] = dict(
                            shed=shed_url.rstrip("/"),
                            repository=name,
                            owner=owner,
                            tools=[tool_id],
                            workflows=[workflow["name"]],
                        )
                    else:
                        if tool_id not in workflows_by_toolshed[repo_identifier]["tools"]:
                            workflows_by_toolshed[repo_identifier]["tools"].append(tool_id)
                        if workflow["name"] not in workflows_by_toolshed[repo_identifier]["workflows"]:
                            workflows_by_toolshed[repo_identifier]["workflows"].append(workflow["name"])
            for repo_tag in workflows_by_toolshed:
                workflows.append(workflows_by_toolshed[repo_tag])
            return workflows, total_matches
        return rval, total_matches

    def invoke_workflow(
        self,
        trans,
        workflow_id,
        payload: InvokeWorkflowPayload,
    ) -> Union[WorkflowInvocationResponse, List[WorkflowInvocationResponse]]:
        if trans.anonymous:
            raise exceptions.AuthenticationRequired("You need to be logged in to run workflows.")
        trans.check_user_activation()
        # Get workflow + accessibility check.
        by_stored_id = not payload.instance
        stored_workflow = self._workflows_manager.get_stored_accessible_workflow(trans, workflow_id, by_stored_id)
        version = payload.version
        if version is None and payload.instance:
            workflow = stored_workflow.get_internal_version_by_id(workflow_id)
        else:
            workflow = stored_workflow.get_internal_version(version)
        run_configs = build_workflow_run_configs(trans, workflow, payload.model_dump(exclude_unset=True))
        is_batch = payload.batch
        if not is_batch and len(run_configs) != 1:
            raise exceptions.RequestParameterInvalidException("Must specify 'batch' to use batch parameters.")

        require_exact_tool_versions = payload.require_exact_tool_versions
        tools = self._workflow_contents_manager.get_all_tools(workflow)
        missing_tools = [
            tool
            for tool in tools
            if not trans.app.toolbox.has_tool(
                tool["tool_id"],
                tool_version=tool["tool_version"],
                tool_uuid=tool["tool_uuid"],
                exact=require_exact_tool_versions,
                user=trans.user,
            )
        ]
        if missing_tools:
            missing_tools_message = "Workflow was not invoked; the following required tools are not installed: "
            if require_exact_tool_versions:
                missing_tools_message += ", ".join(
                    [f"{tool['tool_id']} (version {tool['tool_version']})" for tool in missing_tools]
                )
            else:
                missing_tools_message += ", ".join([tool["tool_id"] for tool in missing_tools])
            raise exceptions.MessageException(missing_tools_message)

        invocations = []
        for run_config in run_configs:
            workflow_scheduler_id = payload.scheduler
            # TODO: workflow scheduler hints
            work_request_params = dict(scheduler=workflow_scheduler_id)
            workflow_invocation = queue_invoke(
                trans=trans,
                workflow=workflow,
                workflow_run_config=run_config,
                request_params=work_request_params,
                flush=False,
            )
            invocations.append(workflow_invocation)

        trans.sa_session.commit()
        encoded_invocations = [WorkflowInvocationResponse(**invocation.to_dict()) for invocation in invocations]
        if is_batch:
            return encoded_invocations
        else:
            return encoded_invocations[0]

    def delete(self, trans, workflow_id):
        workflow_to_delete = self._workflows_manager.get_stored_workflow(trans, workflow_id)
        self._workflows_manager.check_security(trans, workflow_to_delete)
        self._workflows_manager.delete(workflow_to_delete)

    def undelete(self, trans, workflow_id):
        workflow_to_undelete = self._workflows_manager.get_stored_workflow(trans, workflow_id)
        self._workflows_manager.check_security(trans, workflow_to_undelete)
        self._workflows_manager.undelete(workflow_to_undelete)

    def get_versions(self, trans, workflow_id, instance: bool):
        stored_workflow: StoredWorkflow = self._workflows_manager.get_stored_accessible_workflow(
            trans, workflow_id, by_stored_id=not instance
        )
        return [
            {"version": i, "update_time": w.update_time.isoformat(), "steps": len(w.steps)}
            for i, w in enumerate(reversed(stored_workflow.workflows))
        ]

    def invocation_counts(self, trans, workflow_id, instance: bool) -> InvocationsStateCounts:
        stored_workflow: StoredWorkflow = self._workflows_manager.get_stored_accessible_workflow(
            trans, workflow_id, by_stored_id=not instance
        )
        return stored_workflow.invocation_counts()

    def get_workflow_menu(self, trans, payload):
        ids_in_menu = [x.stored_workflow_id for x in trans.user.stored_workflow_menu_entries]
        workflows = self._get_workflows_list(
            trans,
            payload,
        )
        return {"ids_in_menu": ids_in_menu, "workflows": workflows}

    def refactor(
        self,
        trans,
        workflow_id,
        payload,
        instance: bool,
    ) -> RefactorResponse:
        stored_workflow = self._workflows_manager.get_stored_workflow(trans, workflow_id, by_stored_id=not instance)
        return self._workflow_contents_manager.refactor(trans, stored_workflow, payload)

    def show_workflow(self, trans, workflow_id, instance, legacy, version) -> StoredWorkflowDetailed:
        stored_workflow = self._workflows_manager.get_stored_workflow(trans, workflow_id, by_stored_id=not instance)
        if stored_workflow.importable is False and stored_workflow.user != trans.user and not trans.user_is_admin:
            wf_count = 0 if not trans.user else trans.user.count_stored_workflow_user_assocs(stored_workflow)
            if wf_count == 0:
                message = "Workflow is neither importable, nor owned by or shared with current user"
                raise exceptions.ItemAccessibilityException(message)
        if legacy:
            style = "legacy"
        else:
            style = "instance"
        if version is None and instance:
            # A Workflow instance may not be the latest workflow version attached to StoredWorkflow.
            # This figures out the correct version so that we return the correct Workflow and version.
            for i, workflow in enumerate(reversed(stored_workflow.workflows)):
                if workflow.id == workflow_id:
                    version = i
                    break
        detailed_workflow = StoredWorkflowDetailed(
            **self._workflow_contents_manager.workflow_to_dict(trans, stored_workflow, style=style, version=version)
        )
        return detailed_workflow

    def _get_workflows_list(
        self,
        trans: ProvidesUserContext,
        payload,
    ):
        workflows, _ = self.index(trans, payload)
        return workflows

    def __get_full_shed_url(self, url):
        for shed_url in self._tool_shed_registry.tool_sheds.values():
            if url in shed_url:
                return shed_url
        return None

    def execute_workflow_with_wetlands(
        self,
        trans: ProvidesUserContext,
        workflow_id,
        payload: ExecuteWithWetlandsPayload,
    ) -> ExecuteWithWetlandsResponse:
        """
        Execute a workflow using Wetlands environment manager.

        This method:
        1. Retrieves the workflow from the database
        2. Exports it to a .ga file
        3. Calls the execute_workflow module to run it with Wetlands
        4. Returns the execution status and results
        """
        # Get the stored workflow
        stored_workflow = self._workflows_manager.get_stored_accessible_workflow(
            trans, workflow_id, by_stored_id=True
        )

        # Create a temporary directory for workflow execution
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Export workflow to .ga file
            workflow_name = stored_workflow.name
            safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in workflow_name)
            ga_filename = f"Galaxy-Workflow-{safe_name}.ga"
            ga_file_path = temp_path / ga_filename

            # Get workflow dict in 'ga' format
            workflow_dict = self._workflow_contents_manager.workflow_to_dict(
                trans, stored_workflow, style="ga"
            )

            # Write to .ga file
            with open(ga_file_path, "w") as f:
                json.dump(workflow_dict, f, indent=4)

            # Prepare inputs JSON if provided
            inputs_json_path = None
            if payload.inputs_json:
                # Convert Galaxy format inputs to Wetlands format
                converted_inputs = convert_galaxy_inputs_to_wetlands_format(payload.inputs_json, trans)
                if converted_inputs:
                    inputs_json_path = temp_path / "inputs.json"
                    with open(inputs_json_path, "w") as f:
                        json.dump({"inputs": converted_inputs}, f, indent=2)

            # Determine galaxy_root (usually the current working directory or configured path)
            galaxy_root = os.getcwd()

            # Determine tool_conf_xml path
            tool_conf_xml = payload.tool_conf_xml
            if not tool_conf_xml:
                # Try default locations
                possible_paths = [
                    Path(galaxy_root) / "config" / "tool_conf.xml",
                    Path(galaxy_root) / "config" / "tool_conf.xml.sample",
                ]
                for possible_path in possible_paths:
                    if possible_path.exists():
                        tool_conf_xml = str(possible_path)
                        break

            try:
                # Execute the workflow using the execute_workflow module
                log.info(f"Executing workflow {workflow_id} with Wetlands")
                log.info(f"Workflow file: {ga_file_path}")
                log.info(f"Galaxy root: {galaxy_root}")
                log.info(f"Tool conf: {tool_conf_xml}")
                log.info(f"Inputs JSON: {inputs_json_path}")
                log.info(f"Dry run: {payload.dry_run}")

                execute_workflow(
                    workflow_file=str(ga_file_path),
                    tool_conf_xml=tool_conf_xml,
                    galaxy_root=galaxy_root,
                    inputs_json=str(inputs_json_path) if inputs_json_path else None,
                    use_wetlands=True,
                    dry_run=payload.dry_run,
                )

                # If we get here, execution was successful
                status = "dry_run" if payload.dry_run else "success"
                message = (
                    f"Workflow '{workflow_name}' dry run completed successfully"
                    if payload.dry_run
                    else f"Workflow '{workflow_name}' executed successfully with Wetlands"
                )

                return ExecuteWithWetlandsResponse(
                    workflow_file=str(ga_file_path),
                    execution_status=status,
                    message=message,
                    outputs={"working_directory": str(temp_path / "workflow_execution")},
                )

            except Exception as e:
                log.error(f"Error executing workflow with Wetlands: {e}")
                return ExecuteWithWetlandsResponse(
                    workflow_file=str(ga_file_path),
                    execution_status="error",
                    message=f"Error executing workflow: {str(e)}",
                    outputs=None,
                )
