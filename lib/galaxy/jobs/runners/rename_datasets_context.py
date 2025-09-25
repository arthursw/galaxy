from pathlib import Path
from contextlib import ContextDecorator

class RenameDatasets(ContextDecorator):
    def __init__(self, datasets, command_parts):
        self.datasets = datasets
        self.command_parts = command_parts.copy()

    def __enter__(self):
        # Save original names and rename
        for d in self.datasets:
            file_name = d.get_file_name()
            # Rename all datasets, even if not mentionned in the command line since their path could be infered in the tool
            # # If not used in command: do nothing
            # if not any(file_name in cp for cp in self.command_parts): continue
            path = Path(file_name)
            new_path = Path(f'{path}.{d.extension}')
            if not path.name.endswith(d.extension) and not new_path.exists():
                new_path.symlink_to(path)
                # Rename in the command parts if used
                self.command_parts = [cp.replace(str(path), str(new_path)) for cp in self.command_parts]
        return self.command_parts

    def __exit__(self, exc_type, exc_value, traceback):
        # Restore original names
        for d in self.datasets:
            path = Path(d.get_file_name())
            new_path = Path(f'{path}.{d.extension}')
            if not path.name.endswith(d.extension) and new_path.exists() and not path.exists():
                new_path.unlink()
                # Rename in the command parts if used
                self.command_parts = [cp.replace(str(new_path), str(path)) for cp in self.command_parts]
        return False  # don’t suppress exceptions