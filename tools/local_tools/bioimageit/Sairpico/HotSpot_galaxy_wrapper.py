#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool HotSpot"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from HotSpot import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='HotSpot',
    description='Hotspot detection in microscopy images.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input Image')
parser.add_argument('--patch_size', help='Patch size (radius)')
parser.add_argument('--neighborhood_size', help='Neighborhood size (radius)')
parser.add_argument('--p_value', help='p-value for false alarm')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)