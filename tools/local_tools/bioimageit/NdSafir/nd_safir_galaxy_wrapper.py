#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool nd_safir"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from nd_safir import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='nd_safir',
    description='Denoising method dedicated to microscopy image and sequence analysis.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('--type', help='Perform 2D, 3D or 3D + time denoising.')
parser.add_argument('--noise', help='Model used to evaluate the noise variance.')
parser.add_argument('--patch', help='Patch radius. Must be of the form AxB (for 2D) or AxBxC (for 3D) where A, B and C are the patch radius in each dimension.')
parser.add_argument('--noise_factor', help='Noise factor.')
parser.add_argument('--n_iterations', help='Number of iterations.')
parser.add_argument('--time_series', action='store_true', help='Consider the image as a sequence (for 3D only).')
parser.add_argument('--n_frames', help='Number of frames to process in a batch. Use 0 to process everything at once (for 4D only).')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)