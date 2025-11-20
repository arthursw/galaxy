#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool structure_training_dataset"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from structure_training_dataset import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='structure_training_dataset',
    description='Convert the default dataset structure to the training file structure.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('movies_folder', type=Path, help='Input movies folder')
parser.add_argument('--split', help='Splits the dataset in two random sets for training and validation, with --split %% of the movies in the training set, and the rest in the validation set (creates train/ and valid/ folders). Does not split if 0.')
parser.add_argument('movie', type=Path, help='Path to the movie (relative to the movie folder).')
parser.add_argument('merged_segmentation', type=Path, help='Path to the merged segmentation (relative to the movie folder).')
parser.add_argument('merged_annotation', type=Path, help='Path to the merged annotation (relative to the movie folder).')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)