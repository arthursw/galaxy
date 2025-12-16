#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool cellpose_sam_segment"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from cellpose_sam_segment import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='cellpose_sam_segment',
    description='Segment cells with Cellpose SAM.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('--use_gpu', type=str, help='Use GPU (default is CPU).')
parser.add_argument('--channel_axis', help='Channel axis. if None, channels dimension is attempted to be automatically determined.')
parser.add_argument('--z_axis', help='Z axis. if None, 2 dimension is attempted to be automatically determined.')
parser.add_argument('--diameter', help='Estimate of the cell diameters (in pixels).')
parser.add_argument('--flow_threshold', help='Flow error threshold (all cells with errors below threshold are kept) (not used for 3D).')
parser.add_argument('--cellprob_threshold', help='All pixels with value above threshold kept for masks, decrease to find more and larger masks.')
parser.add_argument('--do_3D', type=str, help='Run 3D segmentation on 3D/4D image input.')
parser.add_argument('--flow3D_smooth', help='If do_3D and flow3D_smooth>0, smooth flows with gaussian filter of this stddev.')
parser.add_argument('--min_size', help='All ROIs below this size, in pixels, will be discarded. Defaults to 15.')
parser.add_argument('--max_size_fraction', help='Masks larger than max_size_fraction of total image size are removed. Default is 0.4.')
parser.add_argument('--niter', help='number of iterations for dynamics computation. if None, it is set proportional to the diameter.')
parser.add_argument('segmentation', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Convert string boolean values from Galaxy XML to actual booleans
if hasattr(args, 'use_gpu') and isinstance(args.use_gpu, str):
    args.use_gpu = args.use_gpu.lower() == 'true'
if hasattr(args, 'do_3D') and isinstance(args.do_3D, str):
    args.do_3D = args.do_3D.lower() == 'true'


# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)