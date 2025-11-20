from pathlib import Path
from wetlands.environment_manager import EnvironmentManager
from galaxy import exceptions as galaxy_exceptions

class ThumbnailManager:
    def __init__(self, environment_manager:EnvironmentManager) -> None:
        self.environment_manager = environment_manager
        self.thumnail_environment = self.environment_manager.create('convert_image', {'pip': ["bioio==3.0.0", "pillow==11.1.0", "bioio-ome-zarr", "bioio-ome-tiff", "bioio-czi", "bioio-imageio", "bioio-tifffile", "bioio-tiff-glob", "bioio-bioformats"]})
        self.thumnail_environment.launch()

    def queue_generate_thumbnail(self, dataset, galaxy_root_dir):
        file_path = Path(dataset.get_file_name()).resolve()
        thumbnail_path = (Path.home().resolve() / ".galaxy_thumbnails" / f'{file_path.name}.png').resolve()
        if thumbnail_path.exists():
            return
        self.thumnail_environment.execute('thumbnail_generator', 'queue_generate_thumbnail', (str(file_path), dataset.ext, str(thumbnail_path)))
    
    def get_thumbnail_from_file_path(self, file_path: str):
        """
        Return the thumbnail file located under Path.home() / '.galaxy_thumbnails'`
        for the given file_path. Only the basename of file_path is used to
        avoid path traversal. Returns a tuple of (path, headers) similar to
        other service methods that return files.
        """
        # Use only the basename to avoid accepting directory components from user input.
        name = f'{Path(file_path).name}.png'
        thumbnail_dir = Path.home().resolve() / ".galaxy_thumbnails"
        target = (thumbnail_dir / name).resolve()

        # Ensure the resolved target is within the thumbnail directory to prevent
        # directory traversal via symlinks or crafted paths.
        try:
            thumbnail_dir_resolved = thumbnail_dir.resolve()
            target_relative = target.relative_to(thumbnail_dir_resolved)
        except Exception:
            raise galaxy_exceptions.RequestParameterInvalidException("Invalid thumbnail path.")

        if not target.exists() or not target.is_file():
            raise galaxy_exceptions.ObjectNotFound(f"Could not find thumbnail: {name}")

        headers = {
            "Content-Type": "image/png",
            "Content-Disposition": f'inline; filename="{name}"',
        }
        return str(target), headers