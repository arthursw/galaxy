#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool GibsonLanniPSF"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from GibsonLanniPSF import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='GibsonLanniPSF',
    description='3D Gibson-Lanni PSF.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('--width', help='Image width')
parser.add_argument('--height', help='Image height')
parser.add_argument('--depth', help='Image depth')
parser.add_argument('--wavelength', help='Excitation wavelength (nm)')
parser.add_argument('--psxy', help='Pixel size in XY (nm)')
parser.add_argument('--psz', help='Pixel size in Z (nm)')
parser.add_argument('--na', help='Numerical Aperture')
parser.add_argument('--ni', help='Refractive index immersion')
parser.add_argument('--ns', help='Refractive index sample')
parser.add_argument('--ti', help='Working distance (mum)')
parser.add_argument('output', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)