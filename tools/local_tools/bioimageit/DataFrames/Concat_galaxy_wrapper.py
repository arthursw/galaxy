#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool Concat"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from Concat import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='Concat',
    description='Concat all input DataFrames.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments

# Parse arguments
args = parser.parse_args()
