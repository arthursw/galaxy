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
parser.add_argument('--left_index', type=str, help='Left index')
parser.add_argument('--right_index', type=str, help='Right index')
parser.add_argument('--sort', type=str, help='Sort')
parser.add_argument('--left_suffix', help='Left suffix')
parser.add_argument('--right_suffix', help='Right suffix')

# Parse arguments
args = parser.parse_args()

# Convert string boolean values from Galaxy XML to actual booleans
if hasattr(args, 'left_index') and isinstance(args.left_index, str):
    args.left_index = args.left_index.lower() == 'true'
if hasattr(args, 'right_index') and isinstance(args.right_index, str):
    args.right_index = args.right_index.lower() == 'true'
if hasattr(args, 'sort') and isinstance(args.sort, str):
    args.sort = args.sort.lower() == 'true'

