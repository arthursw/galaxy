#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool stardist_segment"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from stardist_segment import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='stardist_segment',
    description='Segment cells with stardist.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('--model_name', help='The model to use.')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)