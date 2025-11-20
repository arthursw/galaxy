#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool clEsperanto_count_nuclei"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from clEsperanto_count_nuclei import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='clEsperanto_count_nuclei',
    description='Count particles with channels in clEsperanto.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input image path')
parser.add_argument('--spot_sigma', help='Spot sigma')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)