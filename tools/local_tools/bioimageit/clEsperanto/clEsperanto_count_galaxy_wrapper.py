#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool clEsperanto_count"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from clEsperanto_count import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='clEsperanto_count',
    description='Count objects with clEsperanto.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input image path')
parser.add_argument('--sigma_x', help='sigma_x')
parser.add_argument('--sigma_y', help='sigma_y')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)