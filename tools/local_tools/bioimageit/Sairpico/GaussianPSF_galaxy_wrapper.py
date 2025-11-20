#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool GaussianPSF"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from GaussianPSF import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='GaussianPSF',
    description='3D Gaussian PSF.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('--width', help='Image width')
parser.add_argument('--height', help='Image height')
parser.add_argument('--depth', help='Image depth')
parser.add_argument('--sigmaxy', help='PSF width and height')
parser.add_argument('--sigmaz', help='PSF depth')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)