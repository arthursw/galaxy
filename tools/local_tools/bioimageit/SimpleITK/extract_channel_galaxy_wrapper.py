#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool extract_channel"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from extract_channel import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='extract_channel',
    description='Extract an image channel.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('image', type=Path, help='Input image')
parser.add_argument('--channel', help='Channel to extract')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)