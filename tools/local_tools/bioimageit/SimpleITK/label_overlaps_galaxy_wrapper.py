#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool label_overlaps"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from label_overlaps import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='label_overlaps',
    description='Compute label overlap statistics from two label images.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('label1', type=Path, help='Input label image 1')
parser.add_argument('label2', type=Path, help='Input label image 2')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)