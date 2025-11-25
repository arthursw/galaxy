from wetlands.environment_manager import EnvironmentManager

class CodeManager:
    def __init__(self, environment_manager:EnvironmentManager) -> None:
        self.setup_code_server(environment_manager)

    def setup_code_server(self,environment_manager:EnvironmentManager) -> None:
        """Handle the installation and launching of code-server."""

        environment = environment_manager.create("codeserver", {
            'python': '3.10',
            'conda': ['code-server==4.106.2'],
            'pip': []
        })

        # Launch the code-server environment
        commands = [
            'code-server --install-extension opener-0.0.1.vsix', # Install the extension
            'code-server --install-extension ms-python.python',
            'code-server --install-extension ms-python.vscode-python-envs',
            'code-server --install-extension ms-python.debugpy',
            'code-server --disable-workspace-trust --disable-telemetry --auth none --bind-addr 127.0.0.1:32344' # Launch code-server
        ]
        unixCommands = [
            # 'code-server --install-extension ms-python.vscode-pylance', # The ID is not recognized because Pylance is not in the open marketplace, use the .vsix file instead
            # Use if statement to avoid reinstalling Pylance if already installed, it is slow to reinstall (unlike the opener extension)
            '( code-server --list-extensions | grep -q ms-python.vscode-pylance && echo "Pylance already installed" ) || code-server --install-extension ./ms-python.vscode-pylance-2025.9.1.vsix',
        ] + commands
        windowsCommands = [
            'if (-not (code-server --list-extensions | Select-String -Quiet "ms-python.vscode-pylance")) { code-server --install-extension ./ms-python.vscode-pylance-2025.9.1.vsix } else { "Pylance already installed" }'
        ] + commands
        environment.executeCommands({"mac": unixCommands, "linux": unixCommands, "windows": windowsCommands})