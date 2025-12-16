#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool generate_annotation"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from generate_annotation import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='generate_annotation',
    description='Generate annotations from a segmentation.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('segmentation', type=Path, help='Input segmentation (in .h5 format).')
parser.add_argument('--cluster_radius', help='Approximate size in voxel of the objects to cluster. 5 is a good value for events of 400nm on films with a pixel size of 160nm.')
parser.add_argument('--keep_labels_unchanged', type=str, help='By default, bright spots are removed (labels 1 are set to 0) and exocytose events (labels 2) are set to 1. This option skip this step, so labels are kept unchanged.')
parser.add_argument('annotation', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Convert string boolean values from Galaxy XML to actual booleans
if hasattr(args, 'keep_labels_unchanged') and isinstance(args.keep_labels_unchanged, str):
    args.keep_labels_unchanged = args.keep_labels_unchanged.lower() == 'true'


# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)