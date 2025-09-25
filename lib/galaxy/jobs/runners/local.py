"""
Job runner plugin for executing jobs on the local system via the command line.
"""

import io
import logging
from pathlib import Path
import re
import selectors
import shlex
import shutil
import subprocess
import tempfile
import threading
import typing
from galaxy.jobs.runners.local_legacy import LegacyLocalJobRunner
from galaxy.jobs.runners.rename_datasets_context import RenameDatasets
from wetlands.environment_manager import EnvironmentManager
from wetlands.external_environment import ExternalEnvironment
from wetlands._internal.dependency_manager import Dependencies
from wetlands.logger import logger



__all__ = ("LocalJobRunner",)
ENTRY_FUNCTION_NAME = "__galaxy_entry_point__"
logger.setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

class EnvironmentLogger:
    def __init__(self):
        self._stop_event = threading.Event()

    def logStdOut(self, process: subprocess.Popen, file: typing.BinaryIO) -> None:
        """Logs output from the subprocess until stopped."""
        if process is None or process.stdout is None:
            return
        sel = selectors.DefaultSelector()
        sel.register(process.stdout, selectors.EVENT_READ)

        try:
            while not self._stop_event.is_set():
                for key, _ in sel.select(timeout=0.2):  # check every 200ms
                    line = typing.cast(io.TextIOWrapper, key.fileobj).readline()
                    if not line:
                        return
                    line = line.strip()
                    print(line)
                    # file.write(line + "\n")
                    file.write((line + "\n").encode("utf-8", errors="replace"))
                    file.flush()
        except Exception as e:
            file.write((f"Exception in logging thread: {e}\n").encode("utf-8", errors="replace"))
        return
            
    def stop(self):
        self._stop_event.set()

class LocalJobRunner(LegacyLocalJobRunner):
    """
    Wetlands job runner backed by a finite pool of worker threads. FIFO scheduling
    """

    runner_name = "WetlandsRunner"

    def __init__(self, app, nworkers):
        """Initialize the environment manager and the JobRunner"""
        self._environment_manager = EnvironmentManager(debug=True)
        self._environment_lock = threading.Lock()
        # Hard code nworkers to debug, but works with multiple workers
        super().__init__(app, nworkers=1)

    def wrap_main(self, script_path: Path) -> Path | None:
        """
        Duplicate a Python script and move the code inside
        'if __name__ == "__main__":' into a entry point function.
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
        
        if len(main_indices)==0:
            log.debug('No \'if __name__ == "__main__":\' clause found. Script cannot be wrapped.')
            return None
        
        if len(main_indices)>1 or lines[main_indices[0]].lstrip() != lines[main_indices[0]]:
            log.debug('Found multiple \'if __name__ == "__main__":\' clauses, or the clause is indented. Script cannot be wrapped.')
            return None
        main_index = main_indices[0]
        main_call_indices =  [i for i, line in enumerate(lines) if line.strip() == entry_function_call]
        
        for mci in main_call_indices:
            if main_index + 1 == mci:
                log.debug(f"Script is already wrapped, {entry_function_call} is called at {mci}")
                return new_path

        # Find the indentation
        indentation = -1

        # Iterate through the lines *after* the main clause and find the next code line, and set the indentation
        for line in lines[main_index + 1:]:
            stripped_line = line.strip()

            # 3. Skip invalid lines: empty, whitespace-only, or full-line comments
            if not stripped_line or stripped_line.startswith('#'):
                continue

            # 4. We found the first valid line! Now, calculate its indentation.
            # The indentation is the part of the string that's removed by lstrip().
            indentation = line[:-len(line.lstrip())]
        
        new_lines = lines.copy()
        end_index = len(lines)
        
        new_lines[main_index] = f"import sys\n\ndef {ENTRY_FUNCTION_NAME}(args):\n{indentation}sys.argv = args\n"

        for li in range(main_index+3, len(lines)):
            line = lines[li]
            if len(line.lstrip()) == len(line):
                end_index = li
        
        new_lines.insert(end_index, f"\nif __name__ == \"__main__\":\n{indentation}{entry_function_call}\n\n")

        with open(new_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return new_path

    def _execute_with_wetlands(self, job_wrapper, python_script_path, command_parts, stdout_file):

        self.tracker.show_elapsed("_execute_with_wetlands()")
        
        if python_script_path is not None:
            python_script_path = self.wrap_main(python_script_path)
            if python_script_path is None:
                return None

        # tool requirements
        requirements = job_wrapper.tool.requirements.packages.to_list()

        # create an env, this is a duplicate of the Galaxy env, 
        # could be improved in the future, 
        # for example if wetlands accepts to create an env from an existing env path

        # command line has been added to the wrapper by prepare_job()
        # job_file, exit_code_path = self._command_line(job_wrapper)
        conda_deps = []
        for r in requirements:
            if r["type"] != "package": continue
            package = r["name"]
            if package is None: continue
            if "channel" in r and r["channel"] is not None:
                package = r["channel"] + "::" + package
            if "version" in r and r["version"] is not None:
                package = package + "==" + r["version"]
            conda_deps.append(package)
            
        # conda_deps = [r["name"] + "==" + r["version"] if "version" in r else r["name"] for r in requirements if r["type"] == "package"]
        dependencies = Dependencies({"python":"3.11", "conda": conda_deps, "channels": ["bioconda"]})

        environment_name = re.sub(r'[^\w _\-.]', '_', job_wrapper.tool.id)
        
        # job_wrapper.job_io.job.input_datasets[0].dataset.extension
        # job_wrapper.job_io.get_input_datasets()[0].ext
        # extra_files_path

        # Lock to avoid creating twice the same env (wetlands locks the connection)
        with self._environment_lock:

            log.debug(f"Create {environment_name} environment if necessary")

            self.tracker.show_elapsed("   create env")
            environment = typing.cast(ExternalEnvironment, self._environment_manager.create(environment_name, dependencies))
            
            command_parts = [cp.strip() for cp in command_parts]

            if not command_parts[0].startswith("python"):
                return environment
            
            self.tracker.show_elapsed("   launch env")
            if not environment.launched():
                log.debug(f"Launch {environment_name} environment")
                environment.launch(logOutputInThread=False)

            self.tracker.show_elapsed("   execute env")
            log.debug(f"Execute {python_script_path} in {environment_name} with args {command_parts[2:]}")
            environment_logger = EnvironmentLogger()
            thread = threading.Thread(target=environment_logger.logStdOut, args=[environment.process, stdout_file])
            try:
                thread.start()

                # with RenameDatasets(job_wrapper.job_io.get_input_datasets(), command_parts[1:]) as args:
                environment.execute(python_script_path.resolve(), ENTRY_FUNCTION_NAME, (command_parts[1:],))
            except Exception as e:
                raise e
            finally:
                environment_logger.stop()
                thread.join()
            log.debug(f"Execution done")

            self.tracker.show_elapsed("   execution finished")


        return environment

    def queue_job(self, job_wrapper):
        self.tracker.show_elapsed("_prepare_job_local()")
        if not self._prepare_job_local(job_wrapper):
            return

        process = None
        stdout_file = tempfile.NamedTemporaryFile(mode="wb+", suffix="_stdout", dir=job_wrapper.working_directory)
        try:
            if job_wrapper.command_line:
                command_parts = shlex.split(job_wrapper.command_line.replace("\\", ""))

                requirements = job_wrapper.tool.requirements.packages.to_list()
                execute_in_wetlands_env = any("channel" in r and r["channel"] is not None for r in requirements)

                if job_wrapper.tool.is_workflow_compatible:
                    
                    # For non python job which require a non stard conda channel: create the env and execute with the legacy runner
                    if execute_in_wetlands_env and not command_parts[0].startswith("python"):
                        # This just launches the environment, 
                        # it will activated and used by the legacy runner when executing tool_script.sh
                        environment = self._execute_with_wetlands(job_wrapper, None, command_parts, stdout_file)
                        if environment is not None:
                            
                            # Rewrite tool_script.sh so that it first activated the env and then execute the command
                            commands = self._environment_manager.commandGenerator.getActivateEnvironmentCommands(environment.name)
                            commands += [" ".join(command_parts)]
                            with open(Path(job_wrapper.working_directory) / "tool_script.sh", "w") as f:
                                f.write("\n".join(commands))
                                # f.writelines(commands)

                    elif command_parts[0].startswith("python"):
                        python_script_path = Path(command_parts[1])
                        if python_script_path.exists() and python_script_path.suffix == '.py':

                            # Stop at first control operator
                            control_ops = {";", "&", "&&", "||", "|", "|&", "<<", ">>"}
                            python_command_parts = []
                            for cp in command_parts:
                                if cp in control_ops:
                                    if cp == "&&":
                                        # If the command is a python command followed by others (with && otherCommands):
                                        # execute the other commands after the python commmand 
                                        # -> set process to None after python execution
                                        remaining_command_line = "&& ".join(re.split(r"&&[^\S\n]+", job_wrapper.command_line)[1:])
                                        # Check if there are any other control op in the remaining
                                        if any(co in remaining_command_line for co in control_ops):
                                            # If so: do not execute with wetlands
                                            log.debug(f"Do not execute with wetlands because the command is not python only")
                                            python_command_parts = []
                                        else:
                                            # Else execute the python, then execute the remaining with galaxy
                                            job_wrapper.command_line = remaining_command_line
                                            log.debug(f"Execute the python command with wetlands, and the remaining with galaxy")
                                    else:
                                        # Otherwise: do not execute with wetlands
                                        log.debug(f"Do not execute with wetlands because the command is not python only")
                                        python_command_parts = []
                                    break
                                python_command_parts.append(cp)
                            
                            if len(python_command_parts)>0:
                                log.debug(f"Execute {' '.join(python_command_parts)} with wetlands")
                                environment = self._execute_with_wetlands(job_wrapper, python_script_path, python_command_parts, stdout_file)
                                if environment:
                                    # process = environment.process

                                    self.tracker.show_elapsed("   write output and script files")
                                    stdout_path = Path(job_wrapper.working_directory) / 'outputs' / 'tool_stdout'
                                    stderr_path = Path(job_wrapper.working_directory) / 'outputs' / 'tool_stderr'

                                    shutil.copy(stdout_file.name, stdout_path)
                                    # Create an empty stderr file
                                    with open(stderr_path, 'w') as f:
                                        pass
                                    
                                    # This overwrite the tool_script.sh
                                    lines = []
                                    # If the command is a python command followed by others (with && otherCommands):
                                    # execute the other commands -> put the commands in the script to execute
                                    if not job_wrapper.command_line.lstrip().startswith("python"):
                                        lines += [job_wrapper.command_line]
                                    lines += [f"\n\ncat {stdout_path}\n\n", f"cat {stderr_path} 1>&2\n\n"]

                                    with open(Path(job_wrapper.working_directory) / "tool_script.sh", "w") as f:
                                        f.writelines(lines)

                                    process = None

        except Exception as e:
            if stdout_file is not None and not stdout_file.closed:
                stdout_file.close()
            log.debug("exception:")
            log.debug(e)
            log.exception("failure running job %d", job_wrapper.job_id)
            self._fail_job_local(job_wrapper, "failure running job")
            return
                
        self.queue_job_execute(job_wrapper, process, stdout_file)
