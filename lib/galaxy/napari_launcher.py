from multiprocessing.connection import Client
import os
from pathlib import Path
from typing import cast

from wetlands.environment_manager import EnvironmentManager
from wetlands.external_environment import ExternalEnvironment

class NapariLauncher:

    def __init__(self, environment_manager:EnvironmentManager) -> None:
        self.napari_environment_process = None
        self.environment_manager = environment_manager

    def launch_napari(self):
        dependencies = {"python":"3.12", "conda":['conda-forge::napari', 'conda-forge::pyqt'], "pip":[]}
        self.napari_environment: ExternalEnvironment = cast(ExternalEnvironment, self.environment_manager.create('napari', dependencies))
        
        env = os.environ.copy()
        # Uset the QT_API so that napari finds the QT version of the conda env
        if 'QT_API' in env:
            del env['QT_API']

        # check if process is already launched and working
        if self.napari_environment_process is not None and self.napari_environment_process.poll() is None:
            return

        self.napari_environment_process = self.napari_environment.executeCommands([f'python -u "napari_manager.py"'], {"env":env})

        if self.napari_environment_process.stdout is not None:
            try:
                for line in self.napari_environment_process.stdout:
                    if line.strip().startswith("Listening port "):
                        self.port = int(line.strip().replace("Listening port ", ""))
                        break
            except Exception as e:
                self.napari_environment_process.stdout.close()
                raise e

        if self.napari_environment_process.poll() is not None:
            if self.napari_environment_process.stdout is not None:
                self.napari_environment_process.stdout.close()
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