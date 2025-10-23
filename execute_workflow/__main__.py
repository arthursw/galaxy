"""
Allow the execute_workflow package to be run as a module.

Usage:
    python -m execute_workflow workflow.ga
    python -m execute_workflow workflow.ga config/tool_conf.xml.sample
"""

from .main import main

if __name__ == "__main__":
    main()
