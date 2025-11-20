#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool Filter"""

import sys
import argparse
from pathlib import Path
import pandas as pd

# Import the Tool class from the original tool module
from Filter import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='Filter',
    description='Filter out rows containing given values and from given range.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('--column_name', help='Column name')
parser.add_argument('--min', help='The minimum value to keep. Ignored if None (None by default).')
parser.add_argument('--max', help='The maximum value to keep. Ignored if None (None by default).')
parser.add_argument('--numbers_to_remove', help='Comma separated numbers to filter out (for example "0,1,55").')
parser.add_argument('--strings_to_remove', help='Comma separated string to filter out (for example "the,words,to,remove").')
parser.add_argument('--input_dataframe', type=Path, help='Input CSV DataFrame')

# Parse arguments
args = parser.parse_args()

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