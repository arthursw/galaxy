#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool label_statistics"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from label_statistics import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='label_statistics',
    description='Compute label statistics from a label image.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('image', type=Path, help='Input image')
parser.add_argument('label', type=Path, help='Input label')
parser.add_argument('--minSize', help='Min size of the labels')
parser.add_argument('--maxSize', help='Max size of the labels')
parser.add_argument('connected_component', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)