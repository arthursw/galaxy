#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool omero_download"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from omero_download import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='omero_download',
    description='Download files from Omero.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('--dataset_id', help='Dataset ID')
parser.add_argument('out', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processAllData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processAllData([args])