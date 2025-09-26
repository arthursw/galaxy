
import multiprocessing
import numpy as np
from PIL import Image
from bioio import BioImage

_pool = None

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')

def create_thumbnail(image_path, thumbnail_path, size=(128, 128)):
    """
    Load an image using bioio, extract the middle slice if needed,
    normalize it to 0-255, convert to PIL Image, and save a thumbnail.
    
    Parameters
    ----------
    image_path : str
        Path to the input image file.
    thumbnail_path : str
        Path where the thumbnail will be saved.
    size : tuple
        Size of the thumbnail (width, height). Default is (128, 128).
    """
    # Load image
    image = BioImage(image_path)
    data = image.get_image_data("TCZYX")  # numpy array
    
    # Drop singleton dimensions for simplicity
    arr = np.squeeze(data)
    
    # If >2D, take the middle slice along first axis
    if arr.ndim > 2:
        middle_idx = arr.shape[0] // 2
        arr = arr[middle_idx]
    
    # Normalize to 0-255
    arr = arr.astype(np.float32)
    arr -= arr.min()
    if arr.max() != 0:
        arr /= arr.max()
    arr *= 255.0
    arr = arr.astype(np.uint8)
    
    # Convert to PIL image
    img = Image.fromarray(arr)
    
    # Create and save thumbnail
    img.thumbnail(size)
    img.save(thumbnail_path)
    return

def queue_generate_thumbnail(image_path, thumbnail_path, size=(128,128)):
    """
    Submit a single thumbnail task to the pool and return AsyncResult.
    """
    global _pool
    if _pool is None:
        _pool = multiprocessing.Pool(8)
    print(f"Queueing thumbnail for {image_path}")
    return _pool.apply_async(create_thumbnail, (image_path, thumbnail_path, size))