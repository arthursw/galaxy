#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool ColumnRegex"""

import sys
import argparse
from pathlib import Path
import pandas as pd

# Import the Tool class from the original tool module
from ColumnRegex import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='ColumnRegex',
    description='Create columns from a regex.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('--columnName', help='Column name')
parser.add_argument('--regex', help='Regex')
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