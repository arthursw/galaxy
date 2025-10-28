"""
Tool XML Wrapper

This module provides functionality for parsing Galaxy tool XML files
and building command lines from tool parameters.
"""

import logging
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

log = logging.getLogger(__name__)

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
                log.warning(f"Could not parse {xml_path}: {e}")
                continue

    except Exception as e:
        log.error(f"Error parsing tool_conf.xml: {e}")

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
        return command.replace("\\", "")
