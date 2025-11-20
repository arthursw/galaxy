#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool segment"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from segment import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='segment',
    description='Segment exocytosis events.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('movie', type=Path, help='Exocytosis movie (in .h5 format).')
parser.add_argument('model_weights', type=Path, help='Model weigths (in .h5 format).')
parser.add_argument('--patch_size', help='Patch size (the movie is split in cubes of --patch_size before being processed). Must be a multiple of 4.')
parser.add_argument('--visualization', action='store_true', help='Generate visualization images.')
parser.add_argument('segmentation', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)