#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool convert_tiff_to_h5"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from convert_tiff_to_h5 import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='convert_tiff_to_h5',
    description='Convert tiff frames to h5 movie.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('tiff', type=Path, help='Path to the input movie folder. It must contain one tiff file per frame, their names must end with the frame number.')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)