#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool symlink"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from symlink import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='symlink',
    description='Symlink files to the workflow folder.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_movie_folder', type=Path, help='Path to the input movie folder.')
parser.add_argument('movie', type=Path, help='Input movie.')
parser.add_argument('output_movie_folder', type=Path, help='Output file')
parser.add_argument('output_movie', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)