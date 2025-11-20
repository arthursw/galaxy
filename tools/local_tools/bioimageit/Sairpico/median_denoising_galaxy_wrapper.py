#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool median_denoising"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from median_denoising import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='median_denoising',
    description='Median filtering.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input Image')
parser.add_argument('--type', help='Perform 2D, 3D or 3D + time denoising.')
parser.add_argument('--radius_x', help='Radius of the filter in the X direction')
parser.add_argument('--radius_y', help='Radius of the filter in the Y direction')
parser.add_argument('--radius_z', help='Radius of the filter in the Z direction (for 3D and 3D + time only)')
parser.add_argument('--radius_t', help='Radius of the filter in the time direction (for 3D + time only)')
parser.add_argument('--padding', action='store_true', help='Add padding to process border pixels')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)