import argparse
from pathlib import Path
import SimpleITK as sitk
import numpy as np
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Compute label overlap statistics from two label images.")
    parser.add_argument("--label1", required=True, help="Input label image 1 path")
    parser.add_argument("--label2", required=True, help="Input label image 2 path")
    parser.add_argument("--output_csv", required=True, help="Output CSV file with overlap statistics")
    args = parser.parse_args()

    label1_path = Path(args.label1)
    label2_path = Path(args.label2)

    if not label1_path.exists():
        raise FileNotFoundError(f"Error: input label image 1 {args.label1} does not exist.")
    if not label2_path.exists():
        raise FileNotFoundError(f"Error: input label image 2 {args.label2} does not exist.")

    # Read images
    label1 = sitk.ReadImage(str(label1_path), imageIO="TIFFImageIO")
    label2 = sitk.ReadImage(str(label2_path), imageIO="TIFFImageIO")

    # Convert to numpy
    label1_data = sitk.GetArrayFromImage(label1).astype(np.uint64)
    label2_data = sitk.GetArrayFromImage(label2).astype(np.uint64)

    print('Label 1 image shape:', label1_data.shape)
    print('Label 2 image shape:', label2_data.shape)

    records = []
    label1_count = int(label1_data.max() + 1)
    for i in range(label1_count):
        uniques, counts = np.unique(label2_data[label1_data == i], return_counts=True)
        for u, c in zip(uniques, counts):
            records.append(dict(
                image1=str(label1_path),
                image2=str(label2_path),
                label1=int(i),
                label2=int(u),
                overlap=int(c)
            ))

    df = pd.DataFrame.from_records(records)
    df.to_csv(args.output_csv, index=False)

import sys

def __galaxy_entry_point__(args):
    sys.argv = args
    main()
if __name__ == "__main__":
    __galaxy_entry_point__(sys.argv)

