#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool omero_upload"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from omero_upload import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='omero_upload',
    description='Upload data to an Omero database.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('image', type=Path, help='Image to upload')
parser.add_argument('--metadata_columns', help='Metadata columns (for example ["column 1", "column 2"])')
parser.add_argument('--dataset_id', help='Dataset ID (ignored if negative)')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processAllData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processAllData([args])