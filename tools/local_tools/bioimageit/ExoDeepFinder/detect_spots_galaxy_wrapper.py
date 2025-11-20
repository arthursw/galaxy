#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool detect_spots"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from detect_spots import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='detect_spots',
    description='Generate annotations from a segmentation.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('movie_folder', type=Path, help='Input folder containing the movie files (a least a tiff folder containing the movie frames).')
parser.add_argument('tiff', type=Path, help='Path to the folder containing the tiff frames, relative to --movie_folder.')
parser.add_argument('--atlas_args', help='Additional atlas arguments.')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)