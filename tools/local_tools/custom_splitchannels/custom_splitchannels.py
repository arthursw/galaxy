import argparse
import sys

import giatools.io
import skimage.io

def split_image(input_file, c1_file, c2_file, c3_file):
    im = giatools.Image.read(input_file)
    im = im.squeeze_like('XYC')
    skimage.io.imsave(c1_file, im.data[:,:,0])
    skimage.io.imsave(c2_file, im.data[:,:,1])
    skimage.io.imsave(c3_file, im.data[:,:,2])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('c1_file')
    parser.add_argument('c2_file')
    parser.add_argument('c3_file')
    args = parser.parse_args()

    split_image(args.input_file, args.c1_file, args.c2_file, args.c3_file)
