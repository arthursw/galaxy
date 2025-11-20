#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool cudaDecon"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from cudaDecon import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='cudaDecon',
    description='CUDA/C++ implementation of an accelerated Richardson Lucy Deconvolution algorithm.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('psf', type=Path, help='Path to the PSF or OTF file.')
parser.add_argument('--background', help='User-supplied background to subtract. If "auto", the median value of the last Z plane will be used as background.')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)