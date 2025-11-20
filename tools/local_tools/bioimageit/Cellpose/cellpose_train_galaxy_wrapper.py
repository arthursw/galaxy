#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool cellpose_train"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from cellpose_train import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='cellpose_train',
    description='Segment cells with cellpose.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('train_directory', type=Path, help='The directory path containing the training data.')
parser.add_argument('test_directory', type=Path, help='The directory path containing the testing data.')
parser.add_argument('--image_filter', help='The filter for selecting image files.')
parser.add_argument('--mask_filter', help='The filter for selecting mask files.')
parser.add_argument('--look_one_level_down', action='store_true', help='Whether to look for data in subdirectories of train_dir and test_dir.')
parser.add_argument('--model_type', help='Model type. Full built-in models: cyto="cytoplasm model", nuclei="nucleus model", cyto2="cytoplasm model with additional user images", cyto3="super-generalist model". For other built-in models, see https://cellpose.readthedocs.io/en/latest/models.html')
parser.add_argument('--channels', help='Channels to run segementation on. For example: "[0,0]" for grayscale, "[2,3]" for G=cytoplasm and B=nucleus, "[2,1]" for G=cytoplasm and R=nucleus.')
parser.add_argument('--use_gpu', action='store_true', help='Use GPU (default is CPU).')
parser.add_argument('--skip_normalization', action='store_true', help='Whether to skip the data normalization.')
parser.add_argument('--weight_decay', help='Weight decay for the optimizer.')
parser.add_argument('--SDG', action='store_true', help='Whether to use SGD as optimization instead of RAdam.')
parser.add_argument('--learning_rate', help='Learning rate for the training.')
parser.add_argument('--n_epochs', help='Number of times to go through the whole training set during training.')
parser.add_argument('--model_name', help='Name of the new network.')
parser.add_argument('--evaluate', action='store_true', help='Whether to evaluate the model after training.')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)