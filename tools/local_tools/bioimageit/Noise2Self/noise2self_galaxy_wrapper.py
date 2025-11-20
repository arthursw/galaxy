#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool noise2self"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from noise2self import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='noise2self',
    description='Noise2Self - Learning Denoising from Single Noisy Images.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('--model_name', help='The model to use.')
parser.add_argument('--num_of_layers', help='Number of layers in the convolutional network')
parser.add_argument('--masker_width', help='Width of the mask')
parser.add_argument('--iterations', help='Number of iterations during training')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)