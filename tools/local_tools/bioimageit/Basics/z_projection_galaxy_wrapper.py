#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool z_projection"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from z_projection import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='z_projection',
    description='Project the Z axis using min intensity, max intensity, average intensity, sum, standard deviation, median.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('--channel', help='The channel to extract.')
parser.add_argument('--projection_type', help='The projection type.')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)