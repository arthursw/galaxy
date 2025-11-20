#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool generate_segmentation"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from generate_segmentation import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='generate_segmentation',
    description='Generate segmentation from an annotation file.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('movie_folder', type=Path, help='Input folder containing the movie files (a least a movie in h5 format, and an expert annotation file).')
parser.add_argument('movie', type=Path, help='Input movie.')
parser.add_argument('annotation', type=Path, help='Corresponding annotation (.xml generated with napari-exodeepfinder or equivalent, can also be a .csv file).')
parser.add_argument('output_annotation', type=Path, help='Output file')
parser.add_argument('output_segmentation', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)