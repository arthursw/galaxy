#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool generate"""

import sys
import argparse
from pathlib import Path
import pandas as pd

# Import the Tool class from the original tool module
from generate import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='generate',
    description='Generate a DataFrame from the given values, range or space.
See the numpy documentation on array creation routines for more information (arange, linspace, logspace and geomspace, https://numpy.org/doc/stable/reference/generated/numpy.arange.html).',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('--strings', help='Comma separated strings.')
parser.add_argument('--numbers', help='Comma separated values.')
parser.add_argument('--arange', help='Return evenly spaced values within a given interval. (see numpy.arange). Provide the parameters in the form start,stop,step ; for example "0,10,2".')
parser.add_argument('--linspace', help='Return evenly spaced numbers over the specified interval (see numpy.linspace). Provide the parameters in the form start,stop,num,endpoint ; for example "0,10,50,True" or "-5, 5".')
parser.add_argument('--logspace', help='Return numbers spaced evenly on a log scale (see numpy.logspace).')
parser.add_argument('--geomspace', help='Return numbers spaced evenly on a log scale (a geometric progression, see numpy.geomspace).')
parser.add_argument('--columnName', help='Column name')
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