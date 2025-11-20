#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool cudaDecon_deskew"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from cudaDecon_deskew import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='cudaDecon_deskew',
    description='CUDA/C++ implementation of an accelerated Richardson Lucy Deconvolution algorithm.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('--dxdata', help='XY Pixel size of image volume.')
parser.add_argument('--dzdata', help='Z-step size in image volume. In a typical light sheet stage-scanning acquisition, this corresponds to the step size that the stage takes between planes, NOT the final Z-step size between planeds after deskewing along the optical axis of the detection objective.')
parser.add_argument('--angle', help='Deskew angle (usually, angle between sheet and axis of stage motion).')
parser.add_argument('--width', help='If not 0, crop output image to specified width')
parser.add_argument('--shift', help='If not 0, shift image center by this value')
parser.add_argument('--pad_val', help='Value to pad image with when deskewing. If None the median value of the last Z plane will be used.')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)