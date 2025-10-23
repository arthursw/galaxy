"""
Execute Workflow Package

This package provides functionality for executing Galaxy workflows
outside of the Galaxy server environment using Wetlands for
environment management.

Main Components:
- collection: Dataset collection structures and matching logic
- tool_wrapper: Galaxy tool XML parsing and command building
- wetlands_integration: Wetlands environment manager integration
- workflow_executor: Main workflow execution logic
- main: Command-line interface

Usage:
    from execute_workflow import execute_workflow

    execute_workflow(
        workflow_file='workflow.ga',
        tool_conf_xml='config/tool_conf.xml',
        galaxy_root='/path/to/galaxy',
        inputs_json='inputs.json'
    )
"""

from .workflow_executor import execute_workflow
from .collection import (
    CollectionElement,
    DatasetCollection,
    load_workflow_inputs,
    match_collections,
)
from .tool_wrapper import MinimalToolWrapper, parse_tool_conf

__all__ = [
    'execute_workflow',
    'CollectionElement',
    'DatasetCollection',
    'load_workflow_inputs',
    'match_collections',
    'MinimalToolWrapper',
    'parse_tool_conf',
]

__version__ = '0.1.0'
