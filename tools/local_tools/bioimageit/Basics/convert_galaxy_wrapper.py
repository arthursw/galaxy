#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool convert"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from convert import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='convert',
    description='Read and write an image with BioIO.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input image')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)