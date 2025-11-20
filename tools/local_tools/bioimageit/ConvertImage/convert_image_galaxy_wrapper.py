#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool convert_image"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from convert_image import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='convert_image',
    description='Convert image file formats. The extension of the output file specifies the file format to use for the conversion. For example, to convert the input image to png and keep the input name, use "{input_image.stem}.png"',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('--stitch', action='store_true', help='Stitch input files with similar names.')
parser.add_argument('--separate', action='store_true', help='Split RGB images into separate channels.')
parser.add_argument('--merge', action='store_true', help='Combine separate channels into RGB image.')
parser.add_argument('--expand', action='store_true', help='Expand indexed color to RGB.')
parser.add_argument('--bigtiff', action='store_true', help='Force BigTIFF files to be written.')
parser.add_argument('--nobigtiff', action='store_true', help='Do not automatically switch to BigTIFF.')
parser.add_argument('--compression', help='Specify the codec to use when saving images.')
parser.add_argument('--series', help='Specify which image series to convert.')
parser.add_argument('--noflat', action='store_true', help='Do not flatten subresolutions.')
parser.add_argument('--cache', action='store_true', help='Cache the initialized reader.')
parser.add_argument('--cache-dir', type=Path, help='Use the specified directory to store the cached initialized reader. If unspecified, the cached reader will be stored under the same folder as the image file.')
parser.add_argument('----no-sas', action='store_true', help='Do not preserve the OME-XML StructuredAnnotation elements.')
parser.add_argument('map', type=Path, help='Specify file on disk to which name should be mapped.')
parser.add_argument('--range', help='Specify the range of planes to convert. Must be of the form MIN,MAX where MIN is the first plane index and MAX is the last plane index. For example 0,5 will only convert planes 0 to 5. Default will convert every planes.')
parser.add_argument('--nogroup', action='store_true', help='Force multi-file datasets to be read as individual files.')
parser.add_argument('--nolookup', action='store_true', help='Disable the conversion of lookup tables.')
parser.add_argument('--autoscale', action='store_true', help='Automatically adjust brightness and contrast before converting; this may mean that the original pixel values are not preserved.')
parser.add_argument('--overwrite', action='store_true', help='Always overwrite the output file, if it already exists.')
parser.add_argument('--nooverwrite', action='store_true', help='Never overwrite the output file, if it already exists.')
parser.add_argument('--crop', help='Crop images before converting. Must be in the form x,y,w,h.')
parser.add_argument('--channel', help='Only convert the specified channel (indexed from 0).')
parser.add_argument('--z', help='Only convert the specified Z section (indexed from 0).')
parser.add_argument('--timepoint', help='Only convert the specified timepoint (indexed from 0).')
parser.add_argument('--padded', action='store_true', help='Filename indexes for series, z, c and t will be zero padded.')
parser.add_argument('--novalid', action='store_true', help='Will not validate the OME-XML for the output file.')
parser.add_argument('--validate', action='store_true', help='Will validate the generated OME-XML for the output file.')
parser.add_argument('--tilex', help='Image will be converted one tile at a time using the given tile width.')
parser.add_argument('--tiley', help='Image will be converted one tile at a time using the given tile height.')
parser.add_argument('----pyramid-scale', help='Generates a pyramid image with each subsequent resolution level divided by scale.')
parser.add_argument('----pyramid-resolutions', help='Generates a pyramid image with the given number of resolution levels.')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)