"""
Wetlands Environment Manager Integration

This module provides functionality for executing tools using Wetlands
environment manager with conda dependency resolution.
"""

import logging
import re
import shlex
import threading
from pathlib import Path
from typing import cast, Tuple

log = logging.getLogger(__name__)

from wetlands.external_environment import ExternalEnvironment
from wetlands._internal.dependency_manager import Dependencies

def execute_directly(environment, command):
    """Execute a command directly without wrapping."""
    process = environment.executeCommands(command)
    stdout = ""
    if process.stdout is not None:
        for line in process.stdout:
            line = line.strip()
            log.info(line)
            stdout += line + "\n"
    process.wait()
    return process.returncode, stdout


def execute_with_wetlands(environment_manager, tool, command, working_dir) -> Tuple[int, str]:
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

    log.info(f"  Creating/using Wetlands environment: {environment_name}")

    # Create or get existing environment
    environment: ExternalEnvironment = cast(ExternalEnvironment, environment_manager.create(environment_name, dependencies))


    # Check if it's a Python command
    if not command_parts[0].startswith("python"):
        log.warning(f"  Non-Python command, executing directly: {command}")
        return execute_directly(environment, command_parts)

    # Get Python script path
    python_script_path = Path(command_parts[1])
    if not python_script_path.exists() or python_script_path.suffix != '.py':
        log.warning(f"  Python script not found or invalid, executing directly")
        return execute_directly(environment, command_parts)

    # Launch environment if not already running
    if not environment.launched():
        log.info(f"  Launching environment...")
        environment.launch()

    # Create stdout capture
    stdout_content = []

    def process_stdout(env, output_list):
        while True:
            line = env.loggingQueue.get()
            if line is None:
                break
            line = line.strip()
            log.info(f"    {line}")
            output_list.append(line)

    # Start logging thread
    logging_thread = threading.Thread(target=process_stdout, args=[environment, stdout_content])

    try:
        logging_thread.start()
        log.info(f"  Executing script: {python_script_path.name}")
        command_parts = [cp.strip() for cp in command_parts]
        environment.runScript(python_script_path.resolve(), tuple(command_parts[2:]))
        exit_code = 0
    except Exception as e:
        log.error(f"  Error during execution: {e}")
        exit_code = 1
    finally:
        environment.loggingQueue.put(None)
        logging_thread.join()

    return exit_code, "\n".join(stdout_content)
