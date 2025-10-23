"""
Command-line Entry Point

This module provides the command-line interface for executing Galaxy workflows.
"""

import argparse
from .workflow_executor import execute_workflow


def parse_args():
    """
    Parses command-line arguments using argparse.
    """
    parser = argparse.ArgumentParser(
        description="Execute a Galaxy workflow.",
        epilog="""
Examples:
  # Without collection inputs:
  python -m execute_workflow /path/to/Galaxy-Workflow-MultiFish.ga
  python -m execute_workflow workflow.ga config/tool_conf.xml.sample
  python -m execute_workflow workflow.ga config/tool_conf.xml.sample /path/to/galaxy

  # With collection inputs:
  python -m execute_workflow workflow.ga config/tool_conf.xml.sample /path/to/galaxy inputs.json

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
