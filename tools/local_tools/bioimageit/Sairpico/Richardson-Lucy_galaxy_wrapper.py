#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool Richardson-Lucy"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from Richardson-Lucy import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='Richardson-Lucy',
    description='Richardson-Lucy deconvolution.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input', type=Path, help='Input image (x and y axis should ideally be even numbers)')
parser.add_argument('--type', help='Perform 2D, 2D Slice or 3D deconvolution.')
parser.add_argument('--sigma', help='Gaussian PSF width (for 2D and 2D Slice only)')
parser.add_argument('psf', type=Path, help='PSF Image (for 3D only)')
parser.add_argument('--niter', help='Number of iterations')
parser.add_argument('--lambda', help='Regularization parameter (unused in 3D)')
parser.add_argument('--padding', type=str, help='Add padding to process border pixels')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Convert string boolean values from Galaxy XML to actual booleans
if hasattr(args, 'padding') and isinstance(args.padding, str):
    args.padding = args.padding.lower() == 'true'


# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)