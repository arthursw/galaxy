#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool extract_channel_bioio"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from extract_channel_bioio import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='extract_channel_bioio',
    description='Extract an image channel.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input image')
parser.add_argument('--channel', help='Channel to extract')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)