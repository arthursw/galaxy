#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool subtract_images"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from subtract_images import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='subtract_images',
    description='Subtract images.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('image1', type=Path, help='Input image 1')
parser.add_argument('image2', type=Path, help='Input image 2')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)