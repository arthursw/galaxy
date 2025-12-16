from multiprocessing.connection import Client
import os
from pathlib import Path
from typing import cast

from wetlands.environment_manager import EnvironmentManager
from wetlands.external_environment import ExternalEnvironment
from wetlands._internal.dependency_manager import Dependencies

class NapariLauncher:

    def __init__(self, environment_manager:EnvironmentManager) -> None:
        self.napari_environment_process = None
        self.environment_manager = environment_manager

    def launch_napari(self):
        dependencies = Dependencies({"python":"3.12", "conda":['conda-forge::napari', 'conda-forge::pyqt'], "pip":[]})
        self.napari_environment: ExternalEnvironment = cast(ExternalEnvironment, self.environment_manager.create('napari', dependencies))
        
        env = os.environ.copy()
        # Uset the QT_API so that napari finds the QT version of the conda env
        if 'QT_API' in env:
            del env['QT_API']

        # check if process is already launched and working
        if self.napari_environment_process is not None and self.napari_environment_process.poll() is None:
            return

        self.napari_environment_process = self.napari_environment.execute_commands([f'python -u "napari_manager.py"'], popen_kwargs={"env":env})

        # Retrieve the ProcessLogger that was already created and started by executeCommands
        self._process_logger = self.environment_manager.get_process_logger(self.napari_environment_process)
        if self._process_logger is None:
            raise Exception("Failed to retrieve ProcessLogger for module executor process")

        # Wait for port announcement with timeout
        def port_predicate(line: str) -> bool:
            return line.startswith("Listening port ")

        port_line = self._process_logger.wait_for_line(port_predicate, timeout=30)
        if port_line:
            self.port = int(port_line.replace("Listening port ", ""))

        if self.napari_environment_process.poll() is not None:
            raise Exception(f"Process exited with return code {self.napari_environment_process.returncode}.")
        
        if self.port is None:
            raise Exception(f"Could not find the server port.")
        self.napari_connection = Client(("localhost", self.port))

        # self._log_thread = threading.Thread(target=self.log_napari_output)
        # self._log_thread.start()


    def try_open_image_in_napari(self, path, removeExistingImages):
        self.launch_napari()
        try:
            self.napari_connection.send((str(path), removeExistingImages))
        except (EOFError, BrokenPipeError) as e:
            if self.nTries>1:
                raise e
            self.nTries += 1
            self.napari_environment.exit()
            self.try_open_image_in_napari(path, removeExistingImages)

    def open_image_in_napari(self, path, removeExistingImages):
        self.nTries = 0
        self.try_open_image_in_napari(path, removeExistingImages)
    
    def open_image(self, file_path:str, ext:str, remove_existing_images:bool):
        if ext is not None:
            link = Path(file_path).with_suffix("." + ext)
            if not link.exists():
                link.symlink_to(file_path)
            self.open_image_in_napari(link, remove_existing_images)
            headers = {
                "Content-Type": "image/"+ ext,
                "Content-Disposition": f'inline; filename="{link.name}"',
            }
            return  link, headers