#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool binary_threshold"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from binary_threshold import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='binary_threshold',
    description='SimpleITK Binary threshold.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('image', type=Path, help='Input image path')
parser.add_argument('--channel', help='Channel to threshold')
parser.add_argument('--lowerThreshold', help='Lower threshold')
parser.add_argument('--upperThreshold', help='Upper threshold')
parser.add_argument('--insideValue', help='Inside value')
parser.add_argument('--outsideValue', help='Outside value')
parser.add_argument('thresholded_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)