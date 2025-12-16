#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool spitfire"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from spitfire import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='spitfire',
    description='SPITFIR(e) utilizes the primal-dual optimization principle for fast energy minimization. Experimental results in various microscopy modalities from wide field up to lattice light sheet demonstrate the ability of the SPITFIR(e) algorithm to efficiently reduce noise, blur, and out-of-focus background, while avoiding the emergence of deconvolution artifacts.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path. The dimensions (width, height, depth) of the image should be even for best results.')
parser.add_argument('--type', help='Perform 2D, 3D or 4D deconvolution.')
parser.add_argument('--regularization', help='Regularization parameter pow(2,-x).')
parser.add_argument('--weighting', help='Weighting. Regularization parameter pow(2,-x). Must be in range [0.0, 1.0].')
parser.add_argument('--method', help='Method.')
parser.add_argument('--padding', type=str, help='Add a padding to process pixels in borders.')
parser.add_argument('output_image', type=Path, help='Output file')

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