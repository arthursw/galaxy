import os
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from Cheetah.Template import Template
except ImportError:
    raise ImportError("Please install cheetah: pip install cheetah3")


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
                    }
        
        return outputs
    
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


def execute_workflow(workflow_file, tool_conf_xml=None, galaxy_root=None):
    """
    Execute a Galaxy workflow by extracting and running commands independently
    
    Args:
        workflow_file: Path to .ga workflow file
        tool_conf_xml: Path to tool_conf.xml (optional, recommended)
        galaxy_root: Root directory of Galaxy installation (optional, defaults to current working directory)
        
    If tool_conf_xml is provided, it will be parsed to map tool IDs to XML paths.
    Otherwise, it will attempt to find tool_conf.xml in the galaxy_root.
    """
    import json
    
    # Determine galaxy_root
    if galaxy_root is None:
        galaxy_root = os.getcwd()
    
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
    # Track outputs from each step: step_outputs[step_id][output_name] = file_path
    step_outputs = {}
    
    # Process each step in the workflow
    steps = workflow.get('steps', {})
    for step_id in sorted(steps.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        step = steps[step_id]
        step_type = step.get('type')
        tool_id = step.get('tool_id')
        
        # Handle data input steps (no tool_id)
        if not tool_id:
            if step_type == 'data_collection_input' or step_type == 'data_input':
                print(f"Step {step_id}: Input dataset - requires user-provided file path")
                # For input datasets, we'll need to get the file path from user
                # Store a placeholder that indicates this needs to be provided
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
        
        # Extract parameters from step (tool_state contains the parameter values)
        params = step.get('tool_state', {})
        
        # Convert params if they're stored as JSON string
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except:
                params = {}
        
        # Ensure params is a dictionary
        if not isinstance(params, dict):
            params = {}
        
        # Resolve input connections
        input_connections = step.get('input_connections', {})
        if input_connections:
            # Replace ConnectedValue placeholders with actual file paths
            for param_name, connection_info in input_connections.items():
                # connection_info can be a dict or a list of dicts
                if isinstance(connection_info, dict):
                    source_step_id = str(connection_info.get('id'))
                    source_output_name = connection_info.get('output_name', 'output')
                    
                    # Get the output file from the source step
                    if source_step_id in step_outputs:
                        if source_output_name in step_outputs[source_step_id]:
                            input_file = step_outputs[source_step_id][source_output_name]
                            params[param_name] = input_file
                            print(f"  Resolved input '{param_name}' from step {source_step_id}.{source_output_name}: {input_file}")
                        else:
                            print(f"  Warning: Output '{source_output_name}' not found in step {source_step_id}")
                    else:
                        print(f"  Warning: Step {source_step_id} outputs not found")
                elif isinstance(connection_info, list):
                    # Multiple inputs (e.g., for collections)
                    input_files = []
                    for conn in connection_info:
                        source_step_id = str(conn.get('id'))
                        source_output_name = conn.get('output_name', 'output')
                        if source_step_id in step_outputs and source_output_name in step_outputs[source_step_id]:
                            input_files.append(step_outputs[source_step_id][source_output_name])
                    params[param_name] = input_files
        
        # Generate output file paths for this step
        output_files = {}
        for output_name, output_info in tool.outputs.items():
            output_format = output_info.get('format', 'data')
            output_file = f"step_{step_id}_{output_name}.{output_format}"
            output_files[output_name] = output_file
        
        # Store outputs for future steps to reference
        step_outputs[step_id] = output_files
        
        # Build and output command
        try:
            command = tool.build_command(params, output_files=output_files)
            print(f"\n{'='*60}")
            print(f"Step {step_id}: {tool_id}")
            print(f"Command: {command}")
            print(f"{'='*60}")
            
            # Uncomment to actually execute:
            # exit_code = os.system(command)
            # print(f"Exit code: {exit_code}")
            
        except Exception as e:
            print(f"Step {step_id} ({tool_id}): Error building command - {e}")


if __name__ == "__main__":
    import sys
    
    # Example usage
    if len(sys.argv) > 1:
        workflow_file = sys.argv[1]
        tool_conf_xml = sys.argv[2] if len(sys.argv) > 2 else None
        galaxy_root = sys.argv[3] if len(sys.argv) > 3 else None
        execute_workflow(workflow_file, tool_conf_xml, galaxy_root)
    else:
        # Demo with hardcoded paths
        print("Usage: python execute_workflow.py <workflow.ga> [tool_conf.xml] [galaxy_root]")
        print("\nExamples:")
        print("  python execute_workflow.py /Users/amasson/Desktop/Galaxy-Workflow-MultiFish.ga")
        print("  python execute_workflow.py /Users/amasson/Desktop/Galaxy-Workflow-MultiFish.ga config/tool_conf.xml.sample")
        print("  python execute_workflow.py /Users/amasson/Desktop/Galaxy-Workflow-MultiFish.ga config/tool_conf.xml.sample /Users/amasson/Travail/galaxy")
