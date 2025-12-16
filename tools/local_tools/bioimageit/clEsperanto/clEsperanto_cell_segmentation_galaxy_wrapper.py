#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool clEsperanto_cell_segmentation"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from clEsperanto_cell_segmentation import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='clEsperanto_cell_segmentation',
    description='Cell segmentation with clEsperanto.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input image path')
parser.add_argument('--corrected_binary', type=str, help='if non corrected is not good')
parser.add_argument('--radius_x', help='radius_x')
parser.add_argument('--radius_y', help='radius_y')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Convert string boolean values from Galaxy XML to actual booleans
if hasattr(args, 'corrected_binary') and isinstance(args.corrected_binary, str):
    args.corrected_binary = args.corrected_binary.lower() == 'true'


# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)