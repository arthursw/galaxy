#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool cellpose_segment"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from cellpose_segment import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='cellpose_segment',
    description='Segment cells with cellpose.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('--model_type', help='Model type. “cyto”=cytoplasm model; “nuclei”=nucleus model; “cyto2”=cytoplasm model with additional user images; “cyto3”=super-generalist model.')
parser.add_argument('--use_gpu', action='store_true', help='Use GPU (default is CPU).')
parser.add_argument('--auto_diameter', action='store_true', help='Automatically estimate cell diameters, see https://cellpose.readthedocs.io/en/latest/settings.html.')
parser.add_argument('--diameter', help='Estimate of the cell diameters (in pixels).')
parser.add_argument('--channels', help='Channels to run segementation on. For example: "[0,0]" for grayscale, "[2,3]" for G=cytoplasm and B=nucleus, "[2,1]" for G=cytoplasm and R=nucleus.')
parser.add_argument('segmentation', type=Path, help='Output file')
parser.add_argument('visualization', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)