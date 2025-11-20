#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool train"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from train import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='train',
    description='Train a model from the given dataset.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('dataset', type=Path, help='Input dataset')
parser.add_argument('--patch_sizes', help='Patch sizes. Can be an integer or a list of the form [patchSizeModel1, patchSizeModel2, ...]. A list enables to train multiple models, each using the previous weights as initialization. For example, with --patch_sizes "[8, 16]": Model1 will use patches of size 8 voxels and Model2 will use patches of 16 voxels and initialize with the Model1 weights. The longest list of the parameters --patch_sizes, --batch_sizes, --random_shifts, --n_epochs and --n_steps will be use to determine the number of trainings ; and shorter lists will be extended with duplicates of their last values (integer parameters are similarly duplicated) to match the number of trainings.')
parser.add_argument('--batch_sizes', help='Batch sizes. Can be an integer or a list of the form [batchSizeModel1, batchSizeModel2, ...].')
parser.add_argument('--random_shifts', help='Random shifts. Can be an integer or a list of the form [randomShiftsModel1, randomShiftsModel2, ...].')
parser.add_argument('--n_epochs', help='Number of epochs. Can be an integer or a list of the form [nEpochsModel1, nEpochsModel2, ...].')
parser.add_argument('--n_steps', help='Number of steps per epochs. Can be an integer or a list of the form [nStepsModel1, nStepsModel2, ...].')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)