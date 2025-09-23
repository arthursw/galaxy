"""
Job runner plugin for executing jobs on the local system via the command line.
"""

import datetime
import logging
import os
import subprocess
import tempfile
import threading
from time import sleep
from typing import (
    Tuple,
    TYPE_CHECKING,
)

from galaxy import model
from galaxy.job_execution.output_collect import default_exit_code_file
from galaxy.util import asbool
from galaxy.util.commands import new_clean_env

from galaxy.metadata.set_metadata import set_metadata_portable

from . import (
    BaseJobRunner,
    JobState,
)
from .util.process_groups import (
    check_pg,
    kill_pg,
)

if TYPE_CHECKING:
    from galaxy.jobs import MinimalJobWrapper

log = logging.getLogger(__name__)

__all__ = ("LegacyLocalJobRunner",)

DEFAULT_POOL_SLEEP_TIME = 1
# TODO: Set to false and just get rid of this option. It would simplify this
# class nicely. -John
DEFAULT_EMBED_METADATA_IN_JOB = True

class LegacyLocalJobRunner(BaseJobRunner):
    """
    Job runner backed by a finite pool of worker threads. FIFO scheduling
    """

    runner_name = "LocalRunner"

    def __init__(self, app, nworkers):
        """Start the job runner"""

        self._proc_lock = threading.Lock()
        self._procs = []

        self._environ = new_clean_env()

        super().__init__(app, nworkers)

    def _command_line(self, job_wrapper: "MinimalJobWrapper") -> Tuple[str, str]:
        """ """
        command_line = job_wrapper.runner_command_line

        # slots would be cleaner name, but don't want deployers to see examples and think it
        # is going to work with other job runners.
        slots = job_wrapper.job_destination.params.get("local_slots") or os.environ.get("GALAXY_SLOTS")
        if slots:
            slots_statement = f'GALAXY_SLOTS="{int(slots)}"; export GALAXY_SLOTS; GALAXY_SLOTS_CONFIGURED="1"; export GALAXY_SLOTS_CONFIGURED;'
        else:
            slots_statement = 'GALAXY_SLOTS="1"; export GALAXY_SLOTS;'

        job_id = job_wrapper.get_id_tag()
        job_file = JobState.default_job_file(job_wrapper.working_directory, job_id)
        exit_code_path = default_exit_code_file(job_wrapper.working_directory, job_id)
        job_script_props = {
            "slots_statement": slots_statement,
            "command": command_line,
            "exit_code_path": exit_code_path,
            "working_directory": job_wrapper.working_directory,
            "shell": job_wrapper.shell,
        }
        job_file_contents = self.get_job_file(job_wrapper, **job_script_props)
        self.write_executable_script(job_file, job_file_contents, job_io=job_wrapper.job_io)
        return job_file, exit_code_path

    def queue_job(self, job_wrapper):
        if not self._prepare_job_local(job_wrapper):
            return
        self.queue_job_execute(job_wrapper)

    def queue_job_execute(self, job_wrapper, proc: subprocess.Popen | None=None, stdout_file=None, stderr_file=None):
        stderr = stdout = ""

        self.tracker.show_elapsed("   queue_job_execute")
        # command line has been added to the wrapper by prepare_job()
        job_file, exit_code_path = self._command_line(job_wrapper)
        job_id = job_wrapper.get_id_tag()

        set_metadata_directly = stdout_file is not None
        if set_metadata_directly:
            with open(job_file, 'r') as f:
                lines = f.readlines()
            with open(job_file, 'w') as f:
                f.writelines(lines[:-2]+lines[-1:])
        
        execute_process = proc is None
        try:
            if stdout_file is None:
                stdout_file = tempfile.NamedTemporaryFile(mode="wb+", suffix="_stdout", dir=job_wrapper.working_directory)
            if stderr_file is None:
                stderr_file = tempfile.NamedTemporaryFile(mode="wb+", suffix="_stderr", dir=job_wrapper.working_directory)
            log.debug(f"({job_id}) executing job script: {job_file}")

            self.tracker.show_elapsed(f"   execute subprocess {job_file}")
            if proc is None:
                # The preexec_fn argument of Popen() is used to call os.setpgrp() in
                # the child process just before the child is executed. This will set
                # the PGID of the child process to its PID (i.e. ensures that it is
                # the root of its own process group instead of Galaxy's one).
                proc = subprocess.Popen(
                    args=[job_file],
                    cwd=job_wrapper.working_directory,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    env=self._environ,
                    preexec_fn=os.setpgrp,
                )

            self.tracker.show_elapsed(f"   executed subprocess {job_file}")
            proc.terminated_by_shutdown = False
            with self._proc_lock:
                self._procs.append(proc)

            try:
                job = job_wrapper.get_job()
                # Flush job with change_state.
                job_wrapper.set_external_id(proc.pid, job=job, flush=False)
                job_wrapper.change_state(model.Job.states.RUNNING, job=job)
                self._handle_container(job_wrapper, proc)

                self.tracker.show_elapsed(f"   __poll_if_needed")
                terminated = self.__poll_if_needed(proc, job_wrapper, job_id)
                self.tracker.show_elapsed(f"   wait")

                if execute_process:
                    proc.wait()  # reap
                self.tracker.show_elapsed(f"   done")
                if terminated:
                    return
                elif execute_process and check_pg(proc.pid):
                    kill_pg(proc.pid)
            finally:
                with self._proc_lock:
                    self._procs.remove(proc)

            if proc.terminated_by_shutdown:
                self._fail_job_local(job_wrapper, "job terminated by Galaxy shutdown")
                return

            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = self._job_io_for_db(stdout_file)
            stderr = self._job_io_for_db(stderr_file)
            log.debug(f"execution finished: {job_file}")
        except Exception as e:
            log.debug("exception:")
            log.debug(e)
            log.exception("failure running job %d", job_wrapper.job_id)
            self._fail_job_local(job_wrapper, "failure running job")
            return
        finally:
            if stdout_file is not None:
                stdout_file.close()
            if stderr_file is not None:
                stderr_file.close()
        
        self.tracker.show_elapsed(f"   set_metadata_directly")

        if set_metadata_directly:
            set_metadata_portable(job_wrapper.working_directory)

        self.tracker.show_elapsed(f"   _handle_metadata_if_needed")
        self._handle_metadata_if_needed(job_wrapper)

        self.tracker.show_elapsed(f"   _handle_metadata_if_needed finished")

        job_destination = job_wrapper.job_destination
        job_state = JobState(job_wrapper, job_destination)
        job_state.stop_job = False

        self.tracker.show_elapsed(f"   _finish_or_resubmit_job")
        self._finish_or_resubmit_job(job_state, stdout, stderr, job_id=job_id)

    def stop_job(self, job_wrapper):
        # if our local job has JobExternalOutputMetadata associated, then our primary job has to have already finished
        job = job_wrapper.get_job()
        job_ext_output_metadata = job.get_external_output_metadata()
        try:
            pid = job_ext_output_metadata[
                0
            ].job_runner_external_pid  # every JobExternalOutputMetadata has a pid set, we just need to take from one of them
            assert pid not in [None, ""]
        except Exception:
            # metadata internal or job not complete yet
            pid = job.get_job_runner_external_id()
        if pid in [None, ""]:
            log.warning(f"stop_job(): {job.id}: no PID in database for job, unable to stop")
            return
        pid = int(pid)
        if not check_pg(pid):
            log.warning("stop_job(): %s: Process group %d was already dead or can't be signaled", job.id, pid)
            return
        log.debug("stop_job(): %s: Terminating process group %d", job.id, pid)
        kill_pg(pid)

    def recover(self, job, job_wrapper):
        # local jobs can't be recovered
        job_wrapper.change_state(
            model.Job.states.ERROR, info="This job was killed when Galaxy was restarted.  Please retry the job."
        )

    def shutdown(self):
        super().shutdown()
        with self._proc_lock:
            for proc in self._procs:
                proc.terminated_by_shutdown = True
                kill_pg(proc.pid)
                proc.wait()  # reap

    def _fail_job_local(self, job_wrapper, message):
        job_destination = job_wrapper.job_destination
        job_state = JobState(job_wrapper, job_destination)
        job_state.fail_message = message
        job_state.stop_job = False
        self.fail_job(job_state, exception=True)

    def _handle_metadata_if_needed(self, job_wrapper):
        if not self._embed_metadata(job_wrapper):
            self._handle_metadata_externally(job_wrapper, resolve_requirements=True)

    def _embed_metadata(self, job_wrapper):
        job_destination = job_wrapper.job_destination
        if "celery" in job_wrapper.metadata_strategy:
            return False
        embed_metadata = asbool(job_destination.params.get("embed_metadata_in_job", DEFAULT_EMBED_METADATA_IN_JOB))
        return embed_metadata

    def _prepare_job_local(self, job_wrapper):
        return self.prepare_job(job_wrapper, include_metadata=self._embed_metadata(job_wrapper))

    def _handle_container(self, job_wrapper, proc):
        if not job_wrapper.tool.produces_entry_points:
            return

        while check_pg(proc.pid):
            if job_wrapper.check_for_entry_points(check_already_configured=False):
                return

            sleep(0.5)

    def __poll_if_needed(self, proc, job_wrapper, job_id):
        # Only poll if needed (i.e. job limits are set)
        if not job_wrapper.has_limits():
            return

        job_start = datetime.datetime.now()
        i = 0
        pgid = proc.pid
        # Iterate until the process exits, periodically checking its limits
        while check_pg(pgid):
            i += 1
            if (i % 20) == 0:
                limit_state = job_wrapper.check_limits(runtime=datetime.datetime.now() - job_start)
                if limit_state is not None:
                    job_wrapper.fail(limit_state[1])
                    log.debug("(%s) Terminating process group %d", job_id, pgid)
                    kill_pg(pgid)
                    return True
            else:
                sleep(DEFAULT_POOL_SLEEP_TIME)
