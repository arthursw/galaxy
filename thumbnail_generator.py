
import multiprocessing
from pathlib import Path
import traceback
import numpy as np
from PIL import Image
from bioio import BioImage

_pool = None

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')

def create_thumbnail(image_path: str, extension: str, thumbnail_path: str, size=(128, 128)):
    """
    Load an image using bioio, extract the middle slice if needed,
    normalize it to 0-255, convert to PIL Image, and save a thumbnail.
    
    Parameters
    ----------
    image_path : str
        Path to the input image file.
    extension: str
        Path to the image file extension.
    thumbnail_path : str
        Path where the thumbnail will be saved.
    size : tuple
        Size of the thumbnail (width, height). Default is (128, 128).
    """
    # Load image

    image_path_with_extension = Path(image_path).with_suffix(f'.{extension}')
    try:
        if not image_path_with_extension.exists():
            image_path_with_extension.symlink_to(image_path)
        print("generate thumbnail", image_path, thumbnail_path, image_path_with_extension)
        image = BioImage(image_path_with_extension)
        data = image.get_image_data("TCZYX")  # numpy array
            
    finally:
        if image_path_with_extension.exists():
            image_path_with_extension.unlink()
    
    # Get a 2D image: middle time and Z slice
    data = data[data.shape[0]//2, :, data.shape[2]//2, :, :]
    
    # Set dimensions order to XYC for Pillow
    data = data.transpose(1,2,0)
                        
    # Normalize to 0-255
    data = data.astype(np.float32)
    data_min = data.min()
    data_max = data.max()

    if data_max == data_min:
        # Handle constant image to avoid division by zero
        data_normalized = np.zeros_like(data, dtype=np.uint8)
    else:
        # Normalize to 0-1, then scale to 0-255
        data_normalized = (data - data_min) / (data_max - data_min) * 255.0
        data_normalized = data_normalized.astype(np.uint8)
    
    # Convert to PIL image
    if data_normalized.shape[2]>=4:
        img = Image.fromarray(data_normalized, 'RGBA')
    elif data_normalized.shape[2]>=3:
        img = Image.fromarray(data_normalized, 'RGB')
    elif data_normalized.shape[2]>=2:
        img = Image.fromarray(data_normalized, 'LA')
    else:
        img = Image.fromarray(data_normalized.squeeze(), 'L')
    
    # Create and save thumbnail
    img.thumbnail(size)
    Path(thumbnail_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(thumbnail_path)
    return

def _on_error(e):
    """Error callback for multiprocessing tasks."""
    print("\n[ERROR] Exception in worker process:")
    traceback.print_exception(type(e), e, e.__traceback__)

def queue_generate_thumbnail(image_path: str, extension: str, thumbnail_path: str, size=(128,128)):
    """
    Submit a single thumbnail task to the pool and return True.
    """
    global _pool
    if _pool is None:
        _pool = multiprocessing.Pool(8)
    print(f"Queueing thumbnail for {image_path}")
    _pool.apply_async(create_thumbnail, (image_path, extension, thumbnail_path, size), error_callback=_on_error)
    return