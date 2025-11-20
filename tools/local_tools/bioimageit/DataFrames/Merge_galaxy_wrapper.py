#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool Merge"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from Merge import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='Merge',
    description='Merge DataFrames.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('--how', help='How')
parser.add_argument('--on', help='On')
parser.add_argument('--left_on', help='Left on')
parser.add_argument('--right_on', help='Right on')
parser.add_argument('--left_index', action='store_true', help='Left index')
parser.add_argument('--right_index', action='store_true', help='Right index')
parser.add_argument('--sort', action='store_true', help='Sort')
parser.add_argument('--left_suffix', help='Left suffix')
parser.add_argument('--right_suffix', help='Right suffix')

# Parse arguments
args = parser.parse_args()
