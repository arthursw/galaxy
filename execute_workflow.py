import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Union, Optional, cast
from collections import defaultdict
import re
import shlex
import tempfile
import threading

try:
    from Cheetah.Template import Template
except ImportError:
    raise ImportError("Please install cheetah: pip install cheetah3")

from wetlands.environment_manager import EnvironmentManager
from wetlands.external_environment import ExternalEnvironment
from wetlands._internal.dependency_manager import Dependencies

# ============================================================================
# Collection Mapping Data Structures
# ============================================================================

class CollectionElement:
    """Represents a single element in a dataset collection.
    
    Tracks the element identifier (for matching across workflow branches)
    and the actual file path.
    """
    
    def __init__(self, element_identifier: str, dataset_path: str):
        self.element_identifier = element_identifier
        self.dataset_path = dataset_path
    
    def __repr__(self):
        return f"CollectionElement(id='{self.element_identifier}', path='{self.dataset_path}')"


class DatasetCollection:
    """Represents a collection of datasets with a specific structure.
    
    Mimics Galaxy's dataset collection structure to enable workflow
    mapping over collections.
    """
    
    def __init__(self, collection_type: str, elements: List[CollectionElement]):
        self.collection_type = collection_type  # e.g., "list", "paired", "list:paired"
        self.elements = elements
    
    def __repr__(self):
        return f"DatasetCollection(type='{self.collection_type}', elements={len(self.elements)})"
    
    def get_element_identifiers(self) -> List[str]:
        """Return list of element identifiers in order."""
        return [e.element_identifier for e in self.elements]


def parse_tool_conf(tool_conf_path, galaxy_root):
    """
    Parse Galaxy's tool_conf.xml to create a mapping of tool_id -> XML path
    
    Args:
        tool_conf_path: Path to tool_conf.xml file
        galaxy_root: Root directory of Galaxy installation
        
    Returns:
        dict: Mapping of tool_id to absolute XML file path
    """
    tool_map = {}
    
    try:
        tree = ET.parse(tool_conf_path)
        root = tree.getroot()
        
        # Find all <tool> elements
        for tool_elem in root.findall('.//tool'):
            file_attr = tool_elem.get('file')
            if not file_attr:
                continue
            
            # Resolve the XML path relative to galaxy_root
            xml_path = Path(galaxy_root) / 'tools' / file_attr
            if not xml_path.exists():
                continue
            
            # Parse the XML to get the tool ID
            try:
                tool_tree = ET.parse(xml_path)
                tool_root = tool_tree.getroot()
                tool_id = tool_root.get('id')
                
                if tool_id:
                    tool_map[tool_id] = str(xml_path.resolve())
            except Exception as e:
                print(f"Warning: Could not parse {xml_path}: {e}")
                continue
                
    except Exception as e:
        print(f"Error parsing tool_conf.xml: {e}")
    
    return tool_map


class MinimalToolWrapper:
    """Minimal wrapper to get command line from a Galaxy tool"""
    
    def __init__(self, tool_id, tool_xml_path):
        """
        Initialize tool wrapper
        
        Args:
            tool_id: The tool identifier
            tool_xml_path: Path to the tool's XML file
        """
        self.tool_id = tool_id
        self.tool_xml_path = tool_xml_path
        self.tree = ET.parse(self.tool_xml_path)
        self.root = self.tree.getroot()
        self.command_template = self._parse_command()
        self.outputs = self._parse_outputs()
        self.requirements = self._parse_requirements()
    
    def _parse_command(self):
        """Extract the <command> section from tool XML"""
        # Find the command element
        command_elem = self.root.find('command')
        if command_elem is None:
            raise ValueError(f"No <command> section in {self.tool_xml_path}")
        
        # Get the command text (preserve structure, strip outer whitespace)
        command_text = (command_elem.text or "").strip()
        return command_text
    
    def _parse_outputs(self):
        """Extract output definitions from tool XML"""
        outputs = {}
        outputs_elem = self.root.find('outputs')

        if outputs_elem is not None:
            for data_elem in outputs_elem.findall('data'):
                output_name = data_elem.get('name')
                if output_name:
                    # Store output information
                    outputs[output_name] = {
                        'name': output_name,
                        'format': data_elem.get('format', 'data'),
                        'format_source': data_elem.get('format_source'),
                        'metadata_source': data_elem.get('metadata_source'),
                        'from_work_dir': data_elem.get('from_work_dir'),
                    }

        return outputs
    
    def _parse_requirements(self):
        """Extract requirements from tool XML"""
        requirements = []
        requirements_elem = self.root.find('requirements')
        
        if requirements_elem is not None:
            for req_elem in requirements_elem.findall('requirement'):
                req = {
                    'type': req_elem.get('type', 'package'),
                    'name': req_elem.text.strip() if req_elem.text else None,
                    'version': req_elem.get('version'),
                }
                # Check for channel attribute (conda-specific)
                channel = req_elem.get('channel')
                if channel:
                    req['channel'] = channel
                requirements.append(req)
        
        return requirements
    
    def build_command(self, params, working_dir=None, output_files=None):
        """
        Build the actual command line from parameters using Cheetah templating
        
        Args:
            params: dict of parameter values from workflow step
                    Keys are parameter names, values are their values
            working_dir: optional working directory path (added to namespace)
            output_files: optional dict mapping output names to file paths
        
        Returns:
            str: The rendered command line with parameters substituted
            
        Example:
            >>> params = {
            ...     'input': 'input.tif',
            ...     'threshold': '0.5',
            ... }
            >>> output_files = {'output': 'output.tif', 'c1': 'c1.tif'}
            >>> command = wrapper.build_command(params, output_files=output_files)
        """
        # Prepare the namespace for Cheetah template rendering
        namespace = {
            'os': os,
            'str': str,
            'len': len,
            'range': range,
            'list': list,
            'dict': dict,
        }
        namespace.update(params)

        if working_dir:
            namespace['working_dir'] = working_dir

        # Add Galaxy-like variables
        namespace['__tool_directory__'] = str(Path(self.tool_xml_path).parent.resolve())
        
        # Add output file paths to namespace
        # For each output defined in the tool XML, add it to the namespace
        if output_files:
            namespace.update(output_files)
        else:
            # Generate default output file paths based on output definitions
            for output_name, output_info in self.outputs.items():
                if output_name not in namespace:
                    # Create a default output file path
                    output_format = output_info.get('format', 'data')
                    namespace[output_name] = f"output_{output_name}.{output_format}"

        try:
            template = Template(self.command_template, searchList=[namespace])
            command = str(template)
        except Exception as e:
            raise ValueError(
                f"Failed to render command template for {self.tool_id}: {e}\n"
                f"Template: {self.command_template}\n"
                f"Params: {params}\n"
                f"Outputs: {list(self.outputs.keys())}"
            )

        command = ' '.join(command.split())
        return command


# ============================================================================
# Wetlands Integration
# ============================================================================

ENTRY_FUNCTION_NAME = "__galaxy_entry_point__"


def wrap_main(script_path: Path) -> Path:
    """
    Duplicate a Python script and move the code inside
    'if __name__ == "__main__":' into an entry point function.
    Adds an invocation right after the block.
    Safe to run multiple times (idempotent).
    
    Returns the path to the new script.
    """
    new_path = script_path.with_name(f"{script_path.stem}{ENTRY_FUNCTION_NAME}.py")
    if new_path.exists():
        return new_path

    entry_function_call = f"{ENTRY_FUNCTION_NAME}(sys.argv)"

    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    main_clause_pattern = re.compile(r'if\s+__name__\s*==\s*(["\'])__main__\1\s*:')
    main_indices = [i for i, line in enumerate(lines) if main_clause_pattern.match(line.strip())]
    
    if len(main_indices) == 0:
        print(f'  Warning: No \'if __name__ == "__main__":\' clause found. Script cannot be wrapped.')
        return script_path
    
    if len(main_indices) > 1 or lines[main_indices[0]].lstrip() != lines[main_indices[0]]:
        print(f'  Warning: Found multiple \'if __name__ == "__main__":\' clauses, or the clause is indented. Script cannot be wrapped.')
        return script_path
    
    main_index = main_indices[0]
    main_call_indices = [i for i, line in enumerate(lines) if line.strip() == entry_function_call]
    
    for mci in main_call_indices:
        if main_index + 1 == mci:
            print(f"  Script is already wrapped, {entry_function_call} is called at {mci}")
            return new_path

    # Find the indentation
    indentation = ""
    for line in lines[main_index + 1:]:
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue
        indentation = line[:len(line) - len(line.lstrip())]
        break
    
    new_lines = lines.copy()
    end_index = len(lines)
    
    new_lines[main_index] = f"import sys\n\ndef {ENTRY_FUNCTION_NAME}(args):\n{indentation}sys.argv = args\n"

    for li in range(main_index + 3, len(lines)):
        line = lines[li]
        if len(line.lstrip()) == len(line):
            end_index = li
            break
    
    new_lines.insert(end_index, f"\nif __name__ == \"__main__\":\n{indentation}{entry_function_call}\n\n")

    with open(new_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return new_path

def execute_directly(environment, command):
    process = environment.executeCommands([command.replace("\\", "")])
    stdout = "\n".join(process.stdout.readlines()) if process.stdout else ""
    return process.returncode, stdout

def execute_with_wetlands(environment_manager, tool, command, working_dir):
    """
    Execute a command using Wetlands environment manager.
    
    Args:
        environment_manager: EnvironmentManager instance
        tool: MinimalToolWrapper instance with requirements
        command: command (e.g., 'python script.py arg1')
        working_dir: Working directory for execution
        
    Returns:
        Tuple of (exit_code, stdout_content)
    """

    command_parts = shlex.split(command)
    # Build conda dependencies from tool requirements
    conda_deps = []
    for r in tool.requirements:
        if r["type"] != "package":
            continue
        package = r["name"]
        if package is None:
            continue
        if "channel" in r and r["channel"] is not None:
            package = r["channel"] + "::" + package
        if "version" in r and r["version"] is not None:
            package = package + "==" + r["version"]
        conda_deps.append(package)
    
    dependencies = Dependencies({"python": "3.11", "conda": conda_deps, "channels": ["bioconda"]})
    
    # Create environment name from tool ID
    environment_name = re.sub(r'[^\w _\-.]', '_', tool.tool_id)
    
    print(f"  Creating/using Wetlands environment: {environment_name}")
    
    # Create or get existing environment
    environment:ExternalEnvironment = cast(ExternalEnvironment, environment_manager.create(environment_name, dependencies))
    

    # Check if it's a Python command
    if not command_parts[0].startswith("python"):
        print(f"  Warning: Non-Python command, executing directly: {command}")
        return execute_directly(environment, command)
    
    # Get Python script path
    python_script_path = Path(command_parts[1])
    if not python_script_path.exists() or python_script_path.suffix != '.py':
        print(f"  Warning: Python script not found or invalid, executing directly")
        return execute_directly(environment, command_parts)
    
    # Wrap the script
    wrapped_script = wrap_main(python_script_path)
    if wrapped_script == python_script_path:
        print(f"  Warning: Could not wrap script, executing directly")
        return execute_directly(environment, command_parts)
    
    # Launch environment if not already running
    if not environment.launched():
        print(f"  Launching environment...")
        environment.launch(logOutputInThread=False)
    
    # Create stdout capture
    stdout_content = []
    
    def process_stdout(env, output_list):
        while True:
            line = env.loggingQueue.get()
            if line is None:
                break
            line = line.strip()
            print(f"    {line}")
            output_list.append(line)
    
    # Start logging thread
    logging_thread = threading.Thread(target=process_stdout, args=[environment, stdout_content])
    
    try:
        logging_thread.start()
        print(f"  Executing script: {wrapped_script.name}")
        environment.execute(wrapped_script.resolve(), ENTRY_FUNCTION_NAME, (command_parts[1:],))
        exit_code = 0
    except Exception as e:
        print(f"  Error during execution: {e}")
        exit_code = 1
    finally:
        environment.loggingQueue.put(None)
        logging_thread.join()
    
    return exit_code, "\n".join(stdout_content)


# ============================================================================
# Collection Input Parsing and Matching
# ============================================================================

def load_workflow_inputs(input_json_path: str) -> Dict[str, Union[str, DatasetCollection]]:
    """Load workflow inputs from JSON file.
    
    JSON format:
    {
      "inputs": {
        "0": {
          "collection_type": "list",
          "elements": [
            {"identifier": "image_1", "path": "/path/to/image_1.tif"},
            {"identifier": "image_2", "path": "/path/to/image_2.tif"}
          ]
        },
        "1": {
          "path": "/path/to/single_file.txt"
        }
      }
    }
    
    Args:
        input_json_path: Path to JSON file containing workflow inputs
        
    Returns:
        Dict mapping step IDs to either file paths (str) or DatasetCollections
    """
    import json
    
    with open(input_json_path) as f:
        data = json.load(f)
    
    parsed_inputs = {}
    for step_id, input_data in data.get("inputs", {}).items():
        if "collection_type" in input_data:
            # It's a collection
            elements = [
                CollectionElement(e["identifier"], e["path"])
                for e in input_data["elements"]
            ]
            parsed_inputs[step_id] = DatasetCollection(
                input_data["collection_type"],
                elements
            )
        else:
            # Single dataset
            parsed_inputs[step_id] = input_data["path"]
    
    return parsed_inputs


def match_collections(
    step_outputs: Dict[str, Dict[str, Union[str, DatasetCollection]]],
    input_connections: Dict[str, Union[dict, list]]
) -> List[Dict[str, str]]:
    """Match multiple input collections by element identifiers.
    
    This implements Galaxy's collection matching logic: when a tool receives
    multiple collection inputs, it must match elements by their identifiers
    across all collections. This ensures that when workflow branches rejoin,
    the correct datasets are paired together.
    
    Args:
        step_outputs: Dict of previous step outputs (step_id -> output_name -> data)
        input_connections: Dict of input connections for current step
        
    Returns:
        List of dicts mapping input names to file paths for each iteration.
        If no collections are found, returns a single empty dict for one execution.
        
    Example:
        If input_connections has:
          - 'label1' connected to collection [img1.c1, img2.c1, img3.c1]
          - 'label2' connected to collection [cell1, cell2, cell3]
        
        Returns:
          [
            {'label1': 'img1.c1', 'label2': 'cell1'},
            {'label1': 'img2.c1', 'label2': 'cell2'},
            {'label1': 'img3.c1', 'label2': 'cell3'}
          ]
    """
    collections_to_match = {}
    
    # Identify which inputs are collections
    for input_name, connection_info in input_connections.items():
        # Handle both single connection (dict) and multiple connections (list)
        if isinstance(connection_info, list):
            # For now, we'll handle the first connection
            # (multiple connections to same input is a more complex case)
            if not connection_info:
                continue
            connection_info = connection_info[0]
        
        source_step_id = str(connection_info.get('id'))
        source_output_name = connection_info.get('output_name', 'output')
        
        if source_step_id in step_outputs:
            source_data = step_outputs[source_step_id].get(source_output_name)
            if isinstance(source_data, DatasetCollection):
                collections_to_match[input_name] = source_data
    
    if not collections_to_match:
        # No collections to match, single execution with no collection params
        return [{}]
    
    # Verify all collections have same element identifiers
    all_identifiers = None
    collection_names = list(collections_to_match.keys())
    
    for input_name, collection in collections_to_match.items():
        coll_identifiers = collection.get_element_identifiers()
        if all_identifiers is None:
            all_identifiers = coll_identifiers
        elif coll_identifiers != all_identifiers:
            raise ValueError(
                f"Collection element identifiers don't match:\n"
                f"  {collection_names[0]}: {all_identifiers}\n"
                f"  {input_name}: {coll_identifiers}\n"
                f"All collections must have the same element identifiers for mapping."
            )
    
    # Create iteration slices - one per element identifier
    iteration_slices = []
    for i, identifier in enumerate(all_identifiers):
        slice_dict = {}
        for input_name, collection in collections_to_match.items():
            slice_dict[input_name] = collection.elements[i].dataset_path
        slice_dict['__element_identifier__'] = identifier
        iteration_slices.append(slice_dict)
    
    return iteration_slices


def save_step_params(params_file, step_id, iteration_idx, params):
    """Save step parameters to a JSON file for future reference."""
    import json
    import hashlib
    
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
    import json
    import hashlib
    
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
    import json
    
    # Determine galaxy_root
    if galaxy_root is None:
        galaxy_root = os.getcwd()
    
    # Initialize EnvironmentManager if Wetlands is available and requested
    environment_manager = None
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
            os.chdir(step_folder)

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
                    # output_file = f"step_{step_id}_{output_name}_{element_id}.{output_format}"
                    output_filename = f"{output_name}_{element_id}.{output_format}"
                else:
                    # Single iteration
                    # output_file = f"step_{step_id}_{output_name}.{output_format}"
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
            try:
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
                        print(f"    Warning: Command exited with code {exit_code}")
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
                print(f"  Error building/executing command for iteration {iter_idx + 1}: {e}")
                continue
        
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


def parse_args():
    """
    Parses command-line arguments using argparse.
    """
    parser = argparse.ArgumentParser(
        description="Execute a Galaxy workflow.",
        epilog="""
Examples:
  # Without collection inputs:
  python execute_workflow.py /path/to/Galaxy-Workflow-MultiFish.ga
  python execute_workflow.py workflow.ga config/tool_conf.xml.sample
  python execute_workflow.py workflow.ga config/tool_conf.xml.sample /path/to/galaxy

  # With collection inputs:
  python execute_workflow.py workflow.ga config/tool_conf.xml.sample /path/to/galaxy inputs.json

See COLLECTION_MAPPING_IMPLEMENTATION.md for inputs.json format
"""
    )

    # Positional arguments
    parser.add_argument(
        'workflow_file', 
        type=str, 
        help='Path to the Galaxy workflow file (.ga).'
    )
    parser.add_argument(
        'tool_conf_xml', 
        type=str, 
        nargs='?', # Optional
        default=None, 
        help='Path to the tool configuration XML file (e.g., tool_conf.xml.sample).'
    )
    parser.add_argument(
        'galaxy_root', 
        type=str, 
        nargs='?', # Optional
        default=None, 
        help='Path to the Galaxy root directory.'
    )
    parser.add_argument(
        'inputs_json', 
        type=str, 
        nargs='?', # Optional
        default=None, 
        help='Path to the JSON file containing workflow inputs, especially for collections.'
    )

    # Optional flag for dry run
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Perform a dry run: print execution details but do not actually execute the workflow.'
    )

    return parser.parse_args()


def main():
    """Main entry point for command-line usage."""
    args = parse_args()

    execute_workflow(
        workflow_file=args.workflow_file,
        tool_conf_xml=args.tool_conf_xml,
        galaxy_root=args.galaxy_root,
        inputs_json=args.inputs_json,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()