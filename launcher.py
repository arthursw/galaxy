#!/usr/bin/env python
"""
Galaxy Desktop Application Launcher

Handles first-time installation setup, then launches Galaxy in desktop mode.
"""

import sys
import os
import subprocess
from pathlib import Path


class GalaxyDesktopLauncher:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.installed_marker = self.script_dir / "config" / ".galaxy-installed"
        self.venv_path = self.script_dir / ".venv"
        self.python_exe = self.venv_path / "bin" / "python"

    def is_installed(self) -> bool:
        """Check if Galaxy has been installed"""
        return self.installed_marker.exists()

    def run_installation(self) -> bool:
        """Run the installation script (run.sh or run.py)"""
        print("🚀 Galaxy is not installed yet. Running installation...")
        print("-" * 60)

        os.chdir(self.script_dir)

        # Try run.sh first
        if (self.script_dir / "run.sh").exists():
            try:
                result = subprocess.run(
                    ["bash", "run.sh"],
                    check=False
                )
                return result.returncode == 0
            except Exception as e:
                print(f"Error running run.sh: {e}")
                return False
        else:
            # Fallback: implement Python installation logic
            print("run.sh not found, using built-in installation...")
            return self.run_python_installation()

    def run_python_installation(self) -> bool:
        """Fallback installation using Python"""
        try:
            if not self.venv_path.exists():
                print("Creating virtual environment...")
                subprocess.run(
                    [sys.executable, "-m", "venv", str(self.venv_path)],
                    check=True
                )

            print("Installing dependencies...")
            subprocess.run(
                [str(self.python_exe), "-m", "pip", "install", "-r", "requirements.txt"],
                check=True
            )

            print("Installing Node.js and yarn...")
            subprocess.run(
                [str(self.python_exe), "-m", "pip", "install", "nodeenv"],
                check=True
            )

            node_version = (self.script_dir / "client" / ".node_version").read_text().strip()
            subprocess.run(
                [str(self.python_exe), "-m", "nodeenv", "-n", node_version, "-p"],
                cwd=str(self.venv_path),
                check=True
            )

            print("Building Galaxy client...")
            os.chdir(self.script_dir / "client")
            subprocess.run(["npm", "install", "--global", "yarn"], check=True)
            subprocess.run(["yarn", "install"], check=True)
            subprocess.run(["yarn", "run", "build-production-maps"], check=True)
            os.chdir(self.script_dir)

            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def mark_installed(self):
        """Write the installed marker file"""
        self.installed_marker.parent.mkdir(parents=True, exist_ok=True)
        self.installed_marker.write_text(
            "Galaxy installation completed\n"
            f"Installed at: {self.script_dir}\n"
        )
        print(f"✅ Installation marker written to: {self.installed_marker}")

    def launch_galaxy(self):
        """Launch Galaxy in desktop mode"""
        print("🌌 Launching Galaxy Desktop...")
        print("-" * 60)

        os.chdir(self.script_dir)

        # Import and run launch_galaxy_desktop
        import launch_galaxy_desktop

        launcher = launch_galaxy_desktop.GalaxyLauncher(
            dev_mode=False,
            on_ready_callback=self.mark_installed
        )
        launcher.launch()

    def main(self):
        """Main entry point"""
        print("=" * 60)
        print("Galaxy Desktop Application")
        print("=" * 60)

        # Check if already installed
        if not self.is_installed():
            print("\n📦 First-time setup required\n")
            if not self.run_installation():
                print("\n❌ Installation failed!")
                sys.exit(1)

            self.mark_installed()
            print("\n✨ Installation complete!\n")
        else:
            print(f"\n✅ Galaxy already installed\n")

        # Launch Galaxy
        try:
            self.launch_galaxy()
        except KeyboardInterrupt:
            print("\n\n👋 Galaxy shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error launching Galaxy: {e}")
            sys.exit(1)


if __name__ == "__main__":
    launcher = GalaxyDesktopLauncher()
    launcher.main()
