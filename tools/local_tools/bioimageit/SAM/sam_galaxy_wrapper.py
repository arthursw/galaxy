#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool sam"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from sam import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='sam',
    description='SAM 2: Segment Anything in Images and Videos.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('image', type=Path, help='The input image to segment.')
parser.add_argument('--points_per_side', help=' The number of points to be sampled along one side of the image. The total number of points is points_per_side**2.')
parser.add_argument('--pred_iou_thresh', help='A fitering threshold in [0,1], using the model's predicted mask quality.')
parser.add_argument('--stability_score_thresh', help='A filtering threshold in [0,1], using the stability of the mask under changes to the cutoff used to binarize the model's mask predictions.')
parser.add_argument('--stability_score_offset', help='The amount to shift the cutoff when calculated the stability score.')
parser.add_argument('segmentation', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)