#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool cellpose_segment"""

import sys
import argparse
from pathlib import Path

# Add the directory containing this script to the path so we can import cellpose_segment
sys.path.insert(0, str(Path(__file__).parent))

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
parser.add_argument('--use_gpu', type=str, help='Use GPU (default is CPU).')
parser.add_argument('--auto_diameter', type=str, help='Automatically estimate cell diameters, see https://cellpose.readthedocs.io/en/latest/settings.html.')
parser.add_argument('--diameter', help='Estimate of the cell diameters (in pixels).')
parser.add_argument('--channels', help='Channels to run segementation on. For example: "[0,0]" for grayscale, "[2,3]" for G=cytoplasm and B=nucleus, "[2,1]" for G=cytoplasm and R=nucleus.')
parser.add_argument('segmentation', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Unescape Galaxy's bracket sanitization (__ob__ -> [, __cb__ -> ])
def unescape_brackets(value):
    if isinstance(value, str):
        return value.replace('__ob__', '[').replace('__cb__', ']')
    return value

for attr in dir(args):
    if not attr.startswith('_'):
        val = getattr(args, attr)
        if isinstance(val, str):
            setattr(args, attr, unescape_brackets(val))


# Convert string boolean values from Galaxy XML to actual booleans
if hasattr(args, 'use_gpu') and isinstance(args.use_gpu, str):
    args.use_gpu = args.use_gpu.lower() == 'true'
if hasattr(args, 'auto_diameter') and isinstance(args.auto_diameter, str):
    args.auto_diameter = args.auto_diameter.lower() == 'true'


# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)