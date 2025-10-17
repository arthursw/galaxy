import argparse
from pathlib import Path
import SimpleITK as sitk

def main():
    parser = argparse.ArgumentParser(description="Compute connected components in a binary image")
    parser.add_argument("--image", required=True, help="Input image path")
    parser.add_argument("--labeled_image", required=True, help="Output labeled image path")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        raise FileNotFoundError(f"Error: input image {args.image} does not exist.")

    # Read input
    input_image = sitk.ReadImage(image_path, imageIO="TIFFImageIO")

    # Connected components
    labeled_image = sitk.ConnectedComponent(input_image)

    # Save output
    sitk.WriteImage(sitk.Cast(labeled_image, sitk.sitkUInt16), str(args.labeled_image), imageIO="TIFFImageIO")

if __name__ == "__main__":
    main()