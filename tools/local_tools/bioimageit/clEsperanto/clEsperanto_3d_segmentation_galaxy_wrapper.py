#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool clEsperanto_3d_segmentation"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from clEsperanto_3d_segmentation import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='clEsperanto_3d_segmentation',
    description='Segment with clEsperanto.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input image path')
parser.add_argument('--sigma_spot_detection', help='sigma_spot_detection')
parser.add_argument('--sigma_outline', help='sigma_outline')
parser.add_argument('--voxel_size_x', help='voxel_size_x')
parser.add_argument('--voxel_size_y', help='voxel_size_y')
parser.add_argument('--voxel_size_z', help='voxel_size_z')
parser.add_argument('--radius_x', help='radius_x')
parser.add_argument('--radius_y', help='radius_y')
parser.add_argument('--radius_z', help='radius_z')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)