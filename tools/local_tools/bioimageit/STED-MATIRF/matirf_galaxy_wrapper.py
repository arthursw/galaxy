#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool matirf"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from matirf import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='matirf',
    description='3D multi-angle TIRF image deconvolution.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Path to the input image, or input text file for image sequence.')
parser.add_argument('microscope_params', type=Path, help='Microscope parameters (json format)')
parser.add_argument('--depth', help='Depth')
parser.add_argument('--nplanes', help='Number of planes')
parser.add_argument('--lambda', help='Regularization (XY,Z)')
parser.add_argument('--gamma', help='Gamma / time step')
parser.add_argument('--iterations', help='Number of iterations')
parser.add_argument('--reg_type', help='Regularization type')
parser.add_argument('--zmin', help='Z0')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)