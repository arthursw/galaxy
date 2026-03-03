#!/usr/bin/env python
"""
Desktop Galaxy initialization script.

Prepares Galaxy for desktop deployment by:
1. Copying sample configuration files
2. Building the client (web UI)
3. Initializing tool dependencies
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def log(msg):
    """Print message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")


def error(msg):
    """Print error message and exit."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def run_cmd(cmd, cwd=None, description=None):
    """
    Run a command and exit on failure.

    Args:
        cmd: Command as list of strings (for subprocess)
        cwd: Working directory (None = current dir)
        description: Human-readable description for logging
    """
    desc = description or " ".join(cmd)
    log(f"Executing: {desc}")

    try:
        result = subprocess.run(cmd, cwd=cwd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        error(f"Command failed: {desc}\nExit code: {e.returncode}")
    except FileNotFoundError as e:
        error(f"Command not found: {cmd[0]}\n{str(e)}")

def restore_symlinks():
    """Restore symlinks broken by GitHub archive extraction.

    GitHub tarballs/zips don't preserve symlinks — they become plain text
    files containing the relative target path. This function detects them
    and recreates proper symlinks.
    """
    log("Restoring symlinks from archive extraction...")
    restored = 0
    script_dir = Path(__file__).parent.resolve()

    for file_path in script_dir.rglob("*"):
        if not file_path.is_file() or file_path.is_symlink():
            continue
        if file_path.stat().st_size > 256:
            continue
        try:
            content = file_path.read_text(encoding="utf-8").strip()
        except (UnicodeDecodeError, OSError):
            continue
        if not (content.startswith("../") or content.startswith("./")):
            continue
        if "\n" in content:
            continue
        target = (file_path.parent / content).resolve()
        if target.exists() and target != file_path.resolve():
            file_path.unlink()
            file_path.symlink_to(os.path.relpath(target, file_path.parent))
            restored += 1

    log(f"  Restored {restored} symlink(s)")



def copy_sample_files():
    """Copy sample configuration files if they don't exist."""
    log("Copying sample files...")

    samples = [
        ("tool-data/shared/ucsc/builds.txt.sample", "tool-data/shared/ucsc/builds.txt"),
        ("tool-data/shared/ucsc/manual_builds.txt.sample", "tool-data/shared/ucsc/manual_builds.txt"),
    ]

    for sample_path, target_path in samples:
        sample = Path(sample_path)
        target = Path(target_path)

        if not target.exists() and sample.exists():
            log(f"  Initializing {target} from {sample}")
            target.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(sample, target)
        elif target.exists():
            log(f"  {target} already exists, skipping")
        elif not sample.exists():
            log(f"  WARNING: {sample} not found, skipping")

    log("Sample files completed")


def setup_yarn():
    """Install/verify Yarn is available and is version 1.x."""
    log("Setting up Yarn...")

    # Check if yarn is available and what version
    try:
        result = subprocess.run(["yarn", "--version"], capture_output=True, text=True, check=True)
        yarn_version = result.stdout.strip()

        # Check if it's version 1.x (classic yarn)
        if yarn_version.startswith("1."):
            log(f"  Yarn {yarn_version} already installed")
            return
        else:
            log(f"  Yarn {yarn_version} found, but need version 1.x (classic)")
            log(f"  Installing yarn 1.x globally...")
            run_cmd(["npm", "install", "--global", "yarn"], description="Install yarn 1.x")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("  Yarn not found, installing...")
        run_cmd(["npm", "install", "--global", "yarn"], description="Install yarn")


def build_client():
    """Build the Galaxy client (web UI)."""
    log("Building Galaxy client...")

    client_dir = Path("client")
    if not client_dir.exists():
        error(f"Client directory not found: {client_dir}")

    # Setup yarn first
    setup_yarn()

    # Install dependencies
    yarn_opts = "--network-timeout 300000 --check-files"
    run_cmd(
        ["yarn", "install"] + yarn_opts.split(),
        cwd="client",
        description="yarn install (client dependencies)"
    )

    # Build production maps
    run_cmd(
        ["yarn", "run", "build-production-maps"],
        cwd="client",
        description="yarn run build-production-maps"
    )

    log("Client build completed")


def init_tool_dependencies():
    """Initialize tool dependencies."""
    log("Initializing tool dependencies...")

    run_cmd(
        ["python", "./scripts/manage_tool_dependencies.py", "init_if_needed"],
        description="Initialize tool dependencies"
    )

    log("Tool dependencies initialization completed")


def main():
    """Main entry point."""
    # Change to script directory (Galaxy root)
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)
    log(f"Working directory: {os.getcwd()}")

    try:
        # Execute steps in order
        restore_symlinks()
        copy_sample_files()
        build_client()
        init_tool_dependencies()

        log("All steps completed successfully!")
        return 0
    except SystemExit as e:
        # Already logged by error() function
        return e.code
    except Exception as e:
        error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
