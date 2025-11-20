#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool atlas"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from atlas import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='atlas',
    description='ATLAS is a new spot detection method. The spots size is automatically selected and the detection threshold adapts to the local image dynamics.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path. The width and height of the image should be even for best results.')
parser.add_argument('--gaussian_std', help='Standard deviation of the Gaussian window (0 for global threshold).')
parser.add_argument('--p_value', help='P-value to account for the probability of false detection.')
parser.add_argument('--area_lim', help='Remove detections smaller than this area.')
parser.add_argument('--verbose', action='store_true', help='Verbose mode.')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)