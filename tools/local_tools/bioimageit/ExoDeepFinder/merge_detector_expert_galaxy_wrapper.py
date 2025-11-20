#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool merge_detector_expert"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from merge_detector_expert import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='merge_detector_expert',
    description='Merge detector detections with expert annotations.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('movie_folder', type=Path, help='Movie folder.')
parser.add_argument('detector_segmentation', type=Path, help='Detector segmentation (in .h5 format).')
parser.add_argument('expert_segmentation', type=Path, help='Expert segmentation (in .h5 format).')
parser.add_argument('expert_annotation', type=Path, help='Expert annotation (in .xml format).')
parser.add_argument('merged_segmentation', type=Path, help='Output file')
parser.add_argument('merged_annotation', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)