"""
Job runner plugin for executing jobs on the local system via the command line.
"""

from contextlib import contextmanager
import logging
from pathlib import Path
import re
import shlex
import shutil
import tempfile
import threading
import typing
from galaxy.jobs.runners.local_legacy import LegacyLocalJobRunner
from wetlands.external_environment import ExternalEnvironment
from wetlands._internal.dependency_manager import Dependencies


__all__ = ("LocalJobRunner",)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

@contextmanager
def capture_execution_logs(output_file: Path):
    """Context manager to capture all logs during execution to a file."""
    handler = logging.FileHandler(output_file)
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger = logging.getLogger("wetlands")
    logger.addHandler(handler)
    try:
        yield
    finally:
        logger.removeHandler(handler)
        handler.close()

class LocalJobRunner(LegacyLocalJobRunner):
    """
    Wetlands job runner backed by a finite pool of worker threads. FIFO scheduling
    """

    runner_name = "WetlandsRunner"

    def __init__(self, app, nworkers=1):
        """Initialize the environment manager and the JobRunner"""
        self._environment_manager = app.environment_manager
        self._environment_lock = threading.Lock()
        # Hard code nworkers to debug, but works with multiple workers
        super().__init__(app, nworkers=1)

    def _execute_with_wetlands(self, job_wrapper, python_script_path, command_parts, stdout_file):

        self.tracker.show_elapsed("_execute_with_wetlands()")
        
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
                environment.launch()

            self.tracker.show_elapsed("   execute env")
            log.debug(f"Execute {python_script_path} in {environment_name} with args {command_parts[2:]}")
            # environment_logger = EnvironmentLogger()

            try:

                with capture_execution_logs(stdout_file.name):
                    environment.run_script(python_script_path.resolve(), tuple(command_parts[2:]))
            except Exception as e:
                raise e

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
                    
                    # For non python job which require a non standard conda channel: create the env and execute with the legacy runner
                    if execute_in_wetlands_env and not command_parts[0].startswith("python"):
                        # This just launches the environment, 
                        # it will activated and used by the legacy runner when executing tool_script.sh
                        environment = self._execute_with_wetlands(job_wrapper, None, command_parts, stdout_file)
                        if environment is not None:
                            
                            # Rewrite tool_script.sh so that it first activated the env and then execute the command
                            commands = self._environment_manager.command_generator.get_activate_environment_commands(environment)
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
                                    stdout_path = Path(job_wrapper.working_directory) / 'outputs' / 'tool_stdout_tmp'
                                    stderr_path = Path(job_wrapper.working_directory) / 'outputs' / 'tool_stderr_tmp'

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
