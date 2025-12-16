#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool average_label_overlaps"""

import sys
import argparse
from pathlib import Path
import pandas as pd

# Import the Tool class from the original tool module
from average_label_overlaps import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='average_label_overlaps',
    description='Count the number (or average number) of overlapping labels. For example: 3 label2 on label1 number 1, 4 label2 on label1 number 2, etc. If average is true, the average number of label2 per label1 is returned.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('--label1_min', help='The minimum value of label1 to keep. Ignored if None (None by default).')
parser.add_argument('--label1_max', help='The maximum value of label1 to keep. Ignored if None (None by default).')
parser.add_argument('--average', type=str, help='Compute average number of label2 per label1 instead of number of label2 by label1')
parser.add_argument('--input_dataframe', type=Path, help='Input CSV DataFrame')

# Parse arguments
args = parser.parse_args()

# Convert string boolean values from Galaxy XML to actual booleans
if hasattr(args, 'average') and isinstance(args.average, str):
    args.average = args.average.lower() == 'true'


# Create tool instance
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

# Read input DataFrame from CSV
if hasattr(args, 'input_dataframe') and args.input_dataframe:
    dataframe = pd.read_csv(args.input_dataframe)
else:
    dataframe = pd.DataFrame()  # Empty DataFrame

# Call processDataFrame
tool.processDataFrame(dataframe, [args])