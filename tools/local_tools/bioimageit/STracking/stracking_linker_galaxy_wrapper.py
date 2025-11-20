#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool stracking_linker"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from stracking_linker import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='stracking_linker',
    description='Linking of particles detected in stracking.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_csv', type=Path, help='Input csv from a stracking detector')
parser.add_argument('--max_connection_cost', help='Maximum connection cost (squared maximum Euclidean distance that a particle can move between two consecutive frames)')
parser.add_argument('--gap', help='For example if gap=2, particles 2 frames apart can be connected')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)