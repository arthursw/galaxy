#!/usr/bin/env python
"""
Galaxy Desktop Launcher

This script launches Galaxy server and opens it in a native desktop window using pywebview.
This allows users to run Galaxy locally with a desktop application experience.
"""

import sys
import os
import subprocess
import time
import threading
import requests
import webview
from pathlib import Path


class DesktopApi:
    """API exposed to JavaScript for desktop-specific functionality"""

    def __init__(self, window=None):
        """Initialize API with optional window reference for file dialogs"""
        self.window = window

    def select_files(self, multiple=True):
        """Open native file picker using pywebview and return absolute file paths"""
        try:
            if self.window is None:
                print("Error: Window reference not available for file picker")
                return []

            result = self.window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=multiple,
            )

            # result is a list of file paths or None if cancelled
            return list(result) if result else []
        except Exception as e:
            print(f"Error in file picker: {e}")
            return []


class GalaxyLauncher:
    def __init__(self, dev_mode=False, on_ready_callback=None):
        self.galaxy_process = None
        self.client_process = None
        self.dev_mode = dev_mode
        # In dev mode, client runs on 8081 and proxies to Galaxy on 8000
        # In production mode, Galaxy serves everything on 8000
        self.galaxy_url = "http://localhost:8081" if dev_mode else "http://localhost:8000"
        # self.galaxy_url = "http://localhost:8000"
        self.galaxy_api_url = "http://localhost:8000"  # Backend always on 8000
        self.galaxy_ready = False
        self.client_ready = False
        self.script_dir = Path(__file__).parent.absolute()
        self.on_ready_callback = on_ready_callback  # Callback when Galaxy is fully ready

    def start_galaxy_server(self):
        """Start the Galaxy server using uvicorn"""
        print("Starting Galaxy server with uvicorn...")

        # Change to the Galaxy directory
        os.chdir(self.script_dir)

        # Find Python executable in venv
        python_exe = self.script_dir / ".venv" / "bin" / "python"
        if not python_exe.exists():
            print(f"Error: Python executable not found at {python_exe}")
            print("Please ensure the virtual environment is set up correctly.")
            sys.exit(1)

        # Set up environment variables
        env = os.environ.copy()
        config_file = self.script_dir / "config" / "galaxy_debug.yml"
        env["GALAXY_CONFIG_FILE"] = str(config_file)
        env["NODE_ENV"] = "test" if self.dev_mode else "production"

        # Start the server using uvicorn
        self.galaxy_process = subprocess.Popen(
            [
                str(python_exe),
                "-m", "uvicorn",
                "--app-dir", "lib",
                "--factory", "galaxy.webapps.galaxy.fast_factory:factory"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )

        # Start a thread to print server output
        self.output_thread = threading.Thread(target=self._monitor_output, daemon=True)
        self.output_thread.start()

    def _monitor_output(self):
        """Monitor and print Galaxy server output"""
        if self.galaxy_process and self.galaxy_process.stdout:
            for line in self.galaxy_process.stdout:
                print(f"[Galaxy] {line.rstrip()}")
                # Check if server is ready
                if "serving at" in line.lower() or "uvicorn running on" in line.lower():
                    self.galaxy_ready = True

    def _monitor_client_output(self):
        """Monitor and print client dev server output"""
        if self.client_process and self.client_process.stdout:
            for line in self.client_process.stdout:
                print(f"[Client] {line.rstrip()}")
                # Check if client dev server is ready
                if "webpack compiled" in line.lower() or "compiled successfully" in line.lower():
                    self.client_ready = True

    def start_client_dev_server(self):
        """Start the client development server with yarn"""
        print("Starting client development server...")

        # Change to client directory
        client_dir = self.script_dir / "client"
        if not client_dir.exists():
            print(f"Error: Client directory not found at {client_dir}")
            return False

        # Prepare the command with ifnm initialization
        # We need to source the fnm environment and then run yarn
        shell_command = (
            'eval "$(fnm env --use-on-cd --shell zsh)" && '
            'cd client && '
            'yarn run develop'
        )

        print(f"Running: {shell_command}")

        # Start the client dev server using shell
        self.client_process = subprocess.Popen(
            shell_command,
            shell=True,
            executable="/bin/zsh",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=str(self.script_dir)
        )

        # Start a thread to monitor client output
        self.client_output_thread = threading.Thread(target=self._monitor_client_output, daemon=True)
        self.client_output_thread.start()

        return True

    def wait_for_galaxy(self, timeout=180):
        """Wait for Galaxy server to be ready"""
        check_url = self.galaxy_api_url if self.dev_mode else self.galaxy_url
        print(f"Waiting for Galaxy API to be ready at {check_url}...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(check_url, timeout=2)
                if response.status_code == 200:
                    print("Galaxy server is ready!")
                    self.galaxy_ready = True
                    return True
            except requests.exceptions.RequestException:
                pass

            # Check if process died
            if self.galaxy_process and self.galaxy_process.poll() is not None:
                print("Error: Galaxy server process terminated unexpectedly")
                return False

            time.sleep(2)

        print("Timeout waiting for Galaxy server to start")
        return False

    def wait_for_client(self, timeout=180):
        """Wait for client dev server to be ready"""
        if not self.dev_mode:
            return True  # Not needed in production mode

        print(f"Waiting for client dev server to be ready at {self.galaxy_url}...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(self.galaxy_url, timeout=2)
                if response.status_code == 200:
                    print("Client dev server is ready!")
                    self.client_ready = True
                    return True
            except requests.exceptions.RequestException:
                pass

            # Check if process died
            if self.client_process and self.client_process.poll() is not None:
                print("Error: Client dev server process terminated unexpectedly")
                return False

            time.sleep(2)

        print("Timeout waiting for client dev server to start")
        return False

    def create_window(self):
        """Create and show the pywebview window"""
        print("Opening Galaxy desktop window...")

        # Create the API instance
        api = DesktopApi()

        # Create the window with the API exposed
        window = webview.create_window(
            title="Galaxy Workflow System",
            url=self.galaxy_url,
            width=1400,
            height=900,
            resizable=True,
            fullscreen=False,
            min_size=(800, 600),
            js_api=api
        )

        # Set the window reference on the API so it can access create_file_dialog()
        api.window = window

        # Call the ready callback if provided (before showing window)
        if self.on_ready_callback:
            try:
                print("Calling on_ready callback...")
                self.on_ready_callback()
            except Exception as e:
                print(f"Warning: on_ready callback failed: {e}")

        # Start the webview (this blocks until window is closed)
        webview.start(debug=self.dev_mode)

    def cleanup(self):
        """Clean up resources and stop the Galaxy server and client dev server"""
        print("\nShutting down...")

        # Stop client dev server if running
        if self.client_process:
            print("Stopping client dev server...")
            self.client_process.terminate()
            try:
                self.client_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("Force killing client dev server...")
                self.client_process.kill()
                self.client_process.wait()
            print("Client dev server stopped.")

        # Stop Galaxy server
        if self.galaxy_process:
            print("Stopping Galaxy server...")
            self.galaxy_process.terminate()
            try:
                self.galaxy_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("Force killing Galaxy server...")
                self.galaxy_process.kill()
                self.galaxy_process.wait()
            print("Galaxy server stopped.")

        print("Shutdown complete.")

    def launch(self):
        """Launch Galaxy (alias for run, for consistency with launcher.py)"""
        self.run()

    def run(self):
        """Main run method"""
        try:
            # Start Galaxy server
            self.start_galaxy_server()

            # Wait for Galaxy API to be ready
            if not self.wait_for_galaxy():
                print("Failed to start Galaxy server")
                self.cleanup()
                sys.exit(1)

            # Start client dev server if in dev mode
            if self.dev_mode:
                if not self.start_client_dev_server():
                    print("Failed to start client dev server")
                    self.cleanup()
                    sys.exit(1)

                # Wait for client to be ready
                if not self.wait_for_client():
                    print("Failed to start client dev server")
                    self.cleanup()
                    sys.exit(1)

            # Give it a moment to fully initialize
            time.sleep(2)

            print(f"\nGalaxy Desktop ready at {self.galaxy_url}")
            if self.dev_mode:
                print("Running in DEVELOPMENT mode with hot-reload enabled")
                print(f"  - Galaxy API: {self.galaxy_api_url}")
                print(f"  - Client Dev Server: {self.galaxy_url}")
            print()

            # Create and show the window (blocks here)
            self.create_window()

        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Galaxy Desktop Launcher")
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode with client hot-reload (starts yarn dev server on port 8081)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Galaxy Desktop Launcher")
    if args.dev:
        print("MODE: Development (with client hot-reload)")
    else:
        print("MODE: Production")
    print("=" * 60)
    print()

    launcher = GalaxyLauncher(dev_mode=args.dev)
    launcher.run()


if __name__ == "__main__":
    main()
