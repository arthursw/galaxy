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

from wetlands.environment_manager import EnvironmentManager
from wetlands.external_environment import ExternalEnvironment
from wetlands._internal.dependency_manager import Dependencies

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
        log.warning(f'  No \'if __name__ == "__main__":\' clause found. Script cannot be wrapped.')
        return script_path

    if len(main_indices) > 1 or lines[main_indices[0]].lstrip() != lines[main_indices[0]]:
        log.warning(f'  Found multiple \'if __name__ == "__main__":\' clauses, or the clause is indented. Script cannot be wrapped.')
        return script_path

    main_index = main_indices[0]
    main_call_indices = [i for i, line in enumerate(lines) if line.strip() == entry_function_call]

    for mci in main_call_indices:
        if main_index + 1 == mci:
            log.info(f"  Script is already wrapped, {entry_function_call} is called at {mci}")
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

    # Wrap the script
    wrapped_script = wrap_main(python_script_path)
    if wrapped_script == python_script_path:
        log.warning(f"  Could not wrap script, executing directly")
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
        log.info(f"  Executing script: {wrapped_script.name}")
        command_parts = [cp.strip() for cp in command_parts]
        environment.execute(wrapped_script.resolve(), ENTRY_FUNCTION_NAME, (command_parts[1:],))
        exit_code = 0
    except Exception as e:
        log.error(f"  Error during execution: {e}")
        exit_code = 1
    finally:
        environment.loggingQueue.put(None)
        logging_thread.join()

    return exit_code, "\n".join(stdout_content)
