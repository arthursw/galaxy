import argparse
from pathlib import Path
import shutil
import sys

def main():
    parser = argparse.ArgumentParser(description='Run Cellpose segmentation')
    parser.add_argument('--input_image', required=True)
    parser.add_argument('--segmentation', required=True)
    parser.add_argument('--use_gpu', default='False')
    parser.add_argument('--channel_axis', default=None)
    parser.add_argument('--z_axis', default=None)
    parser.add_argument('--diameter', default=None)
    parser.add_argument('--flow_threshold', type=float, default=0.4)
    parser.add_argument('--cellprob_threshold', type=float, default=0.0)
    parser.add_argument('--do_3D', default='False')
    parser.add_argument('--flow3D_smooth', type=int, default=0)
    parser.add_argument('--min_size', type=int, default=15)
    parser.add_argument('--max_size_fraction', type=float, default=0.4)
    parser.add_argument('--niter', default=None)
    args = parser.parse_args()

    # convert some args from strings to proper types
    use_gpu = args.use_gpu.lower() == 'true'
    do_3D = args.do_3D.lower() == 'true'
    channel_axis = None if args.channel_axis in (None, '', 'None') else int(args.channel_axis)
    z_axis = None if args.z_axis in (None, '', 'None') else int(args.z_axis)
    diameter = None if args.diameter in (None, '', 'None') else float(args.diameter)
    niter = None if args.niter in (None, '', 'None') else int(args.niter)

    print('[[1/5]] Load Cellpose model')
    from cellpose import models
    from cellpose.io import imread, save_masks

    model = models.CellposeModel(gpu=use_gpu)

    print(f'[[2/5]] Read image {args.input_image}')
    link = Path(f'{args.input_image}.tif')
    link.symlink_to(args.input_image)
    image = imread(link)

    print('[[3/5]] Run segmentation')
    masks, flows, styles = model.eval(
        image,
        channel_axis=channel_axis,
        z_axis=z_axis,
        diameter=diameter,
        flow_threshold=args.flow_threshold,
        cellprob_threshold=args.cellprob_threshold,
        do_3D=do_3D,
        flow3D_smooth=args.flow3D_smooth,
        min_size=args.min_size,
        max_size_fraction=args.max_size_fraction,
        niter=niter,
    )

    input_image = Path(args.input_image)
    output_path = Path(args.segmentation)

    print(f'[[4/5]] Save masks to {output_path}')
    save_masks(image, masks, flows, input_image, tif=True)

    # Cellpose save_masks saves by default to *_cp_masks.tif next to the input image
    generated_mask = input_image.parent / f'{input_image.stem}_cp_masks.tif'
    if generated_mask.exists():
        if output_path.exists():
            output_path.unlink()
        shutil.move(generated_mask, output_path)
        print(f'Saved segmentation: {output_path}')
    else:
        print('Segmentation not generated (no masks found).')
        sys.exit(1)

import sys

def __galaxy_entry_point__(args):
    sys.argv = args
    main()

if __name__ == "__main__":
    __galaxy_entry_point__(sys.argv)

