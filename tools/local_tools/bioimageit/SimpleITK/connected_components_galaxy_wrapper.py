#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool connected_components"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from connected_components import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='connected_components',
    description='Compute connected components in the given binary image.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('image', type=Path, help='Input image path')
parser.add_argument('labeled_image', type=Path, help='Output file')
parser.add_argument('labeled_image_rgb', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)