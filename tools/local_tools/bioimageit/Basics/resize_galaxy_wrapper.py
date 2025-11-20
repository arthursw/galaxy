#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool resize"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from resize import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='resize',
    description='Resize an image either to given dimensions or by a scale factor.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input image path')
parser.add_argument('--width', help='Target width (in pixels). If not provided, computed from scale or original size.')
parser.add_argument('--height', help='Target height (in pixels). If not provided, computed from scale or original size.')
parser.add_argument('--depth', help='Target depth (in pixels, for 3D images). If not provided, computed from scale or original size.')
parser.add_argument('--scale', help='Scaling factor. Ignored if width/height/depth are all specified.')
parser.add_argument('--interpolation', help='Interpolation method: nearest, linear, bspline, lanczos, or label')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)