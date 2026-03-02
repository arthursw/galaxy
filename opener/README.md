# Opener

This VS Code extension runs a small server which listens for commands to open files, folders or workspaces.
It listens on `127.0.0.1:60351`.

You can open files, folders or workspaces from the outside with a simple request.

## Usage Example

For example from Python:

```python
import os
import requests

port = 60351
url = f"http://127.0.0.1:{port}/open"

def open_path(path, target_type="file", new_window=False):
    """
    target_type: 'file', 'folder', or 'workspace'
    new_window: If True, tries to open in a new browser tab/window
    """
    # Normalize path for Windows/Linux consistency
    abs_path = os.path.abspath(path)
    
    params = {
        "path": abs_path,
        "type": target_type,
        "new_window": "true" if new_window else "false"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f"[Success] Opened {target_type}: {abs_path}")
        else:
            print(f"[Error] Server replied: {response.text}")
    except requests.exceptions.ConnectionError:
        print("[Error] Could not connect to code-server. Is the extension loaded?")


# 1. Open a File (Seamless, NO reload)
# Works for .py, .txt, .json, etc.
open_path("./app.py", target_type="file")

# 2. Open a Folder (Triggers Window Reload)
# VS Code: will refresh to show this folder as the root
open_path("/path/to/project", target_type="folder")

# 3. Open a Workspace (Triggers Window Reload)
# Opens a .code-workspace configuration
open_path("./project.code-workspace", target_type="workspace")
```
