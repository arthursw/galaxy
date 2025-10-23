"""
Workflow Executor

This module contains the main workflow execution logic, including
step parameter tracking, output handling, and collection mapping.
"""

import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Union, Optional

from wetlands.environment_manager import EnvironmentManager

from .collection import DatasetCollection, CollectionElement, load_workflow_inputs, match_collections
from .tool_wrapper import MinimalToolWrapper, parse_tool_conf
from .wetlands_integration import execute_with_wetlands


def save_step_params(params_file, step_id, iteration_idx, params):
    """Save step parameters to a JSON file for future reference."""
    params_dict = {}

    # Create a hashable representation of params
    params_hash = hashlib.md5(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()

    if params_file.exists():
        with open(params_file, 'r') as f:
            params_dict = json.load(f)

    key = f"{step_id}_{iteration_idx}"
    params_dict[key] = {"hash": params_hash, "params": params}

    with open(params_file, 'w') as f:
        json.dump(params_dict, f, indent=2)


def check_params_and_outputs(params_file, step_id, iteration_idx, params, output_files):
    """Check if step was already executed with same parameters and outputs exist."""
    if not params_file.exists():
        return False

    try:
        with open(params_file, 'r') as f:
            params_dict = json.load(f)
    except:
        return False

    key = f"{step_id}_{iteration_idx}"
    if key not in params_dict:
        return False

    # Check if parameters match
    params_hash = hashlib.md5(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()
    saved_hash = params_dict[key].get("hash")

    if params_hash != saved_hash:
        return False

    # Check if all output files exist
    for output_path in output_files.values():
        if isinstance(output_path, str) and not Path(output_path).exists():
            return False

    return True


def execute_workflow(workflow_file, tool_conf_xml=None, galaxy_root=None, inputs_json=None, use_wetlands=True, dry_run=False):
    """
    Execute a Galaxy workflow by extracting and running commands independently.
    Supports collection mapping for iterating over dataset collections.

    Args:
        workflow_file: Path to .ga workflow file
        tool_conf_xml: Path to tool_conf.xml (optional, recommended)
        galaxy_root: Root directory of Galaxy installation (optional, defaults to current working directory)
        inputs_json: Path to JSON file with workflow inputs (optional)
        use_wetlands: Whether to use Wetlands for execution (default: True)
        dry_run: Only print commands, do not execute them

    If tool_conf_xml is provided, it will be parsed to map tool IDs to XML paths.
    Otherwise, it will attempt to find tool_conf.xml in the galaxy_root.

    If inputs_json is provided, it should contain dataset paths and collection definitions.
    """
    # Determine galaxy_root
    if galaxy_root is None:
        galaxy_root = os.getcwd()

    # Initialize EnvironmentManager if Wetlands is requested
    environment_manager = None
    if use_wetlands:
        print("Initializing Wetlands EnvironmentManager...")
        environment_manager = EnvironmentManager(debug=True)
        print("EnvironmentManager initialized")

    # Create working directory for workflow execution
    working_dir = Path(galaxy_root).resolve() / "workflow_execution"
    working_dir.mkdir(exist_ok=True)
    print(f"Working directory: {working_dir}")

    # File to track executed step parameters
    params_file = working_dir / ".step_params.json"

    # Load user inputs if provided
    user_inputs = {}
    if inputs_json:
        print(f"Loading workflow inputs from: {inputs_json}")
        user_inputs = load_workflow_inputs(inputs_json)
        print(f"Loaded inputs for {len(user_inputs)} step(s)")

    # Try to find and parse tool configuration
    tool_map = {}
    if tool_conf_xml is None:
        # Try to find tool_conf.xml in standard locations
        possible_paths = [
            Path(galaxy_root) / 'config' / 'tool_conf.xml',
            Path(galaxy_root) / 'config' / 'tool_conf.xml.sample',
        ]
        for possible_path in possible_paths:
            if possible_path.exists():
                tool_conf_xml = str(possible_path)
                break

    if tool_conf_xml and Path(tool_conf_xml).exists():
        print(f"Loading tool configuration from: {tool_conf_xml}")
        tool_map = parse_tool_conf(tool_conf_xml, galaxy_root)
        print(f"Found {len(tool_map)} tools in configuration")
    else:
        print("Warning: No tool_conf.xml found. Tool lookup may fail for tools with non-standard paths.")

    try:
        with open(workflow_file) as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"Error loading workflow: {e}")
        return

    tool_cache = {}
    # Track outputs from each step: step_outputs[step_id][output_name] = file_path or DatasetCollection
    step_outputs: Dict[str, Dict[str, Union[str, DatasetCollection]]] = {}

    # Process each step in the workflow
    steps = workflow.get('steps', {})
    try:
        for step_id in sorted(steps.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            step = steps[step_id]
            step_type = step.get('type')
            tool_id = step.get('tool_id')

            # Handle data input steps (no tool_id)
            if not tool_id:
                if step_type == 'data_collection_input' or step_type == 'data_input':
                    if step_id in user_inputs:
                        input_data = user_inputs[step_id]
                        step_outputs[step_id] = {'output': input_data}
                        if isinstance(input_data, DatasetCollection):
                            print(f"Step {step_id}: Input collection ({input_data.collection_type}) with {len(input_data.elements)} elements")
                        else:
                            print(f"Step {step_id}: Input dataset: {input_data}")
                    else:
                        print(f"Step {step_id}: Input dataset - requires user-provided file path")
                        step_outputs[step_id] = {'output': 'INPUT_FILE_PLACEHOLDER'}
                else:
                    print(f"Step {step_id}: No tool_id found (type: {step_type})")
                continue

            # Load tool if not cached
            if tool_id not in tool_cache:
                # First try to find the tool in the tool map
                tool_xml_path = None
                if tool_id in tool_map:
                    tool_xml_path = Path(tool_map[tool_id])
                else:
                    # Fall back to guessing based on tool ID
                    # Try common patterns
                    possible_paths = [
                        Path(galaxy_root) / 'tools' / 'local_tools' / tool_id / f"{tool_id}.xml",
                        Path(galaxy_root) / 'tools' / tool_id / f"{tool_id}.xml",
                    ]
                    for possible_path in possible_paths:
                        if possible_path.exists():
                            tool_xml_path = possible_path
                            break

                if tool_xml_path is None or not tool_xml_path.exists():
                    print(f"Step {step_id} ({tool_id}): Tool XML not found")
                    tool_cache[tool_id] = None
                    continue

                try:
                    tool_cache[tool_id] = MinimalToolWrapper(tool_id, str(tool_xml_path))
                except Exception as e:
                    print(f"Step {step_id} ({tool_id}): Failed to load tool - {e}")
                    tool_cache[tool_id] = None
                    continue

            tool = tool_cache.get(tool_id)
            if tool is None:
                continue

            # Extract base parameters from step (tool_state contains the parameter values)
            base_params = step.get('tool_state', {})

            # Convert params if they're stored as JSON string
            if isinstance(base_params, str):
                try:
                    base_params = json.loads(base_params)
                except:
                    base_params = {}

            # Ensure params is a dictionary
            if not isinstance(base_params, dict):
                base_params = {}

            # Get input connections for collection matching
            input_connections = step.get('input_connections', {})

            # Match collections - this returns iteration slices
            iteration_slices = match_collections(step_outputs, input_connections)

            num_iterations = len(iteration_slices)
            print(f"\nStep {step_id}: {tool_id}")
            if num_iterations > 1:
                print(f"  Collection mapping: {num_iterations} iterations")

            # Collect output elements across all iterations
            output_collections: Dict[str, List[CollectionElement]] = defaultdict(list)

            # Initialize output files dict (for the case of single iteration)
            iter_output_files = {}

            # Execute tool once per iteration slice
            for iter_idx, slice_dict in enumerate(iteration_slices):
                # Build params for this iteration
                iter_params = base_params.copy()

                # Get element identifier for this iteration
                element_id = slice_dict.get('__element_identifier__', f"element_{iter_idx}")

                # Resolve input connections for this iteration
                for param_name, connection_info in input_connections.items():
                    # Handle both single connection (dict) and multiple connections (list)
                    conn_info = connection_info
                    if isinstance(connection_info, list):
                        if not connection_info:
                            continue
                        conn_info = connection_info[0]

                    # Check if this input is in the slice (collection input)
                    if param_name in slice_dict:
                        iter_params[param_name] = slice_dict[param_name]
                    else:
                        # Non-collection input, resolve normally
                        source_step_id = str(conn_info.get('id'))
                        source_output_name = conn_info.get('output_name', 'output')

                        if source_step_id in step_outputs:
                            if source_output_name in step_outputs[source_step_id]:
                                source_data = step_outputs[source_step_id][source_output_name]
                                # If source is a collection but this param wasn't in slice,
                                # we shouldn't be here, but handle gracefully
                                if isinstance(source_data, DatasetCollection):
                                    print(f"  Warning: Expected collection input '{param_name}' not in slice")
                                else:
                                    iter_params[param_name] = source_data

                # Generate output file paths for this iteration
                # Create output folder for this step
                step_folder = working_dir / "outputs"/ f"step{step_id}_{tool_id}"
                step_folder.mkdir(parents=True, exist_ok=True)

                # Save original directory and change to step folder
                original_dir = os.getcwd()
                os.chdir(step_folder)

                try:
                    iter_output_files = {}
                    for output_name, output_info in tool.outputs.items():
                        output_format = output_info.get('format', 'data')

                        # Check if format should be inherited from format_source
                        format_source = output_info.get('format_source')
                        if format_source and format_source in iter_params:
                            input_file = iter_params[format_source]
                            # Extract extension from input file
                            if isinstance(input_file, str) and '.' in input_file:
                                output_format = input_file.rsplit('.', 1)[1]
                            else:
                                output_format = 'tiff'  # Default for image data
                        elif output_format == 'input' or output_format == 'data':
                            # If format is 'input' or defaults to 'data', try to infer from any input
                            for param_name, param_value in iter_params.items():
                                if isinstance(param_value, str) and '.' in param_value:
                                    # Assume this is an input file
                                    output_format = param_value.rsplit('.', 1)[1]
                                    break
                            else:
                                # Keep 'data' as default only if we couldn't infer anything
                                if output_format == 'data':
                                    output_format = 'tiff'  # Default fallback for image data

                        if num_iterations > 1:
                            # Multiple iterations - include element identifier
                            output_filename = f"{output_name}_{element_id}.{output_format}"
                        else:
                            # Single iteration
                            output_filename = f"{output_name}.{output_format}"

                        output_file = step_folder / f"{output_filename}"

                        iter_output_files[output_name] = str(output_file)

                        # Collect for building output collections
                        if num_iterations > 1:
                            output_collections[output_name].append(
                                CollectionElement(element_id, str(output_file))
                            )

                    # Check if step was already executed with same parameters and outputs exist
                    if check_params_and_outputs(params_file, step_id, iter_idx, iter_params, iter_output_files):
                        if num_iterations > 1:
                            print(f"  Iteration {iter_idx + 1}/{num_iterations} (element: {element_id}): SKIPPED (already executed)")
                        else:
                            print(f"  SKIPPED (already executed)")
                        continue

                    # Build and execute command
                    command = tool.build_command(iter_params, output_files=iter_output_files)
                    if num_iterations > 1:
                        print(f"  Iteration {iter_idx + 1}/{num_iterations} (element: {element_id}):")
                        print(f"    Command: {command}")
                    else:
                        print(f"  Command: {command}")

                    if not dry_run:
                        # Execute the command
                        if environment_manager is not None:
                            # Use Wetlands for execution
                            exit_code, stdout = execute_with_wetlands(
                                environment_manager,
                                tool,
                                command,
                                working_dir
                            )
                        else:
                            # Fall back to direct execution
                            exit_code = os.system(command)

                        if exit_code != 0:
                            raise RuntimeError(f"Command exited with code {exit_code}")
                        else:
                            # Handle from_work_dir outputs - rename files to expected paths
                            for output_name, expected_path in iter_output_files.items():
                                output_info = tool.outputs.get(output_name)
                                if output_info and output_info.get('from_work_dir'):
                                    from_work_dir = output_info['from_work_dir']
                                    actual_file = step_folder / from_work_dir
                                    expected_file = Path(expected_path)

                                    if actual_file.exists() and actual_file.resolve() != expected_file.resolve():
                                        # Rename it to the expected path with element identifier
                                        actual_file.rename(expected_file)
                                        print(f"    Renamed: {from_work_dir} -> {expected_file.name}")

                            # Save parameters on successful execution
                            save_step_params(params_file, step_id, iter_idx, iter_params)

                except Exception as e:
                    print(f"  ERROR during step {step_id} iteration {iter_idx + 1}: {e}")
                    raise
                finally:
                    # Restore original directory
                    os.chdir(original_dir)

            # Store outputs for future steps
            step_outputs[step_id] = {}
            if num_iterations > 1:
                # Multiple iterations - create collections for outputs
                for output_name, elements in output_collections.items():
                    step_outputs[step_id][output_name] = DatasetCollection(
                        collection_type='list',
                        elements=elements
                    )
            else:
                # Single iteration - store as regular files
                step_outputs[step_id] = iter_output_files

            print(f"{'='*60}")

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"WORKFLOW EXECUTION FAILED")
        print(f"{'='*60}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return
