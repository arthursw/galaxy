#!/usr/bin/env python3
"""Galaxy wrapper for PyFlow Tool cimg_denoising"""

import sys
import argparse
from pathlib import Path

# Import the Tool class from the original tool module
from cimg_denoising import Tool

# Create argument parser
parser = argparse.ArgumentParser(
    prog='cimg_denoising',
    description='Denoise 2D+T images corrupted by Gaussian or Poisson noise with patch based methods and basic methods and variational methods.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# Add arguments
parser.add_argument('input_image', type=Path, help='The input image path.')
parser.add_argument('--first', help='Number of the first image (0: default value)')
parser.add_argument('--last', help='Number of the last image (depth or time: default value)')
parser.add_argument('--alpha', help='Alpha mixing of input/output images [0. - 1.] (0.: default value)')
parser.add_argument('--scale', help='Resize the volume in the range [0.5 - 1.5] (1.: default value)')
parser.add_argument('--range', help='Automatic intensity scaling (-1) or manual scaling')
parser.add_argument('--algo', help='Algorithm name')
parser.add_argument('--ng', help='Add artificial Gaussian noise before applying the algorithm')
parser.add_argument('--np', type=str, help='Add artificial Poisson noise before applying the algorithm')
parser.add_argument('--msg', help='Adjust manually the assumed Gaussian noise standard deviation')
parser.add_argument('--stab', type=str, help='Variance stabilization for Poisson noise removal')
parser.add_argument('--patch', help='Half size of the patch (NLMeans, PEWA, OWF, SAFIR, DCT, Wiener)')
parser.add_argument('--neigh', help='Half size of the neighborhood (NLMeans, PEWA, OWF, SAFIR, DCT, Median, Bilateral)')
parser.add_argument('--denoisep', help='Denoising parameter (NLMeans: 3.5 | DCT: 3.0 | Wiener: 1.25 | Bilateral: 2.0 | Gaussian: 1.0 | TV: 6.0 | SV: 6.0 | HV: 6.0)')
parser.add_argument('--sparsep', help='Sparsity parameter (SV and HV algorithms) in the range [0.1 - 0.9]')
parser.add_argument('--iter', help='Number of iterations (NDSafir only)')
parser.add_argument('output_image', type=Path, help='Output file')

# Parse arguments
args = parser.parse_args()

# Convert string boolean values from Galaxy XML to actual booleans
if hasattr(args, 'np') and isinstance(args.np, str):
    args.np = args.np.lower() == 'true'
if hasattr(args, 'stab') and isinstance(args.stab, str):
    args.stab = args.stab.lower() == 'true'


# Create tool instance and call processData
tool = Tool()

if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)