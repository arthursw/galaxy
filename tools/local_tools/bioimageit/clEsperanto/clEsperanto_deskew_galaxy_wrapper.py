#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool clEsperanto_deskew"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from clEsperanto_deskew import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='clEsperanto_deskew',
    description='Deskew with clEsperanto.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input image path')
parser.add_argument('--angle', help='Deskewing angle in degrees')
parser.add_argument('--voxel_size_x', help='voxel_size_x_in_microns')
parser.add_argument('--voxel_size_y', help='voxel_size_y_in_microns')
parser.add_argument('--voxel_size_z', help='voxel_size_z_in_microns')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)