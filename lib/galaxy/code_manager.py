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
            'code-server --install-extension detachhead.basedpyright',
            'code-server --disable-workspace-trust --disable-telemetry --auth none --bind-addr 127.0.0.1:32344' # Launch code-server
        ]
        environment.execute_commands(commands)