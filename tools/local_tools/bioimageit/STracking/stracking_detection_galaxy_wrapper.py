#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool stracking_detection"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from stracking_detection import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='stracking_detection',
    description='Scientific library track particles in 2D+t and 3D+t images. Detection using Difference of Hessians, Laplacian of Gaussian and Difference of Gaussians.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='Input Image')
parser.add_argument('--detector_type', help='Type of Stracking detection, using DoH (Difference of Hessians), LoG (Laplacian of Gaussian) or DoG (Difference of Gaussians)')
parser.add_argument('--min_sigma', help='Minimal sigma value')
parser.add_argument('--max_sigma', help='Maximal sigma value')
parser.add_argument('--n_sigmas', help='Number of sigmas (for DoH and LoG)')
parser.add_argument('--threshold', help='Threshold')
parser.add_argument('--ratio', help='Sigma ratio (for DoG)')
parser.add_argument('--overlap', help='Overlap')
parser.add_argument('--log_scale', action='store_true', help='Log scale (for DoH and LoG)')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)