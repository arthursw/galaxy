#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool LabelsMeasure"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from LabelsMeasure import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='LabelsMeasure',
    description='LabelsMeasure provides the tools to generate the regions of interest from label images.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('label', type=Path, help='Label image path, from cellpose for instance.')
parser.add_argument('--pixel', help='Size of the pixel erosion')
parser.add_argument('--binary_map', action='store_true', help='If false, labels in your black & white image')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)