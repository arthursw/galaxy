from pathlib import Path
import SimpleITK as sitk

class Tool:

    name = "Resize image"
    description = "Resize an image either to given dimensions or by a scale factor."
    categories = ['SimpleITK']
    inputs = [
        dict(
            name='input_image',
            help='Input image path',
            type='Path',
            required=True,
            autoColumn=True,
        ),
        dict(
            name='width',
            help='Target width (in pixels). If not provided, computed from scale or original size.',
            type='int',
            default=None,
        ),
        dict(
            name='height',
            help='Target height (in pixels). If not provided, computed from scale or original size.',
            type='int',
            default=None,
        ),
        dict(
            name='depth',
            help='Target depth (in pixels, for 3D images). If not provided, computed from scale or original size.',
            type='int',
            default=None,
        ),
        dict(
            name='scale',
            help='Scaling factor. Ignored if width/height/depth are all specified.',
            type='float',
            default=None,
        ),
        dict(
            name='interpolation',
            help='Interpolation method: nearest, linear, bspline, lanczos, or label',
            type='str',
            default='linear',
            choices=['nearest', 'linear', 'bspline', 'lanczos', 'label'],
        ),
    ]
    outputs = [
        dict(
            name='output_image',
            help='Resized output image',
            default='{input_image.stem}_resized{input_image.exts}',
            type='Path',
        ),
    ]

    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')

        inputImage = sitk.ReadImage(str(args.input_image))

        # Original size and spacing
        original_size = inputImage.GetSize()
        original_spacing = inputImage.GetSpacing()

        # Determine target size
        if args.width is not None or args.height is not None or args.depth is not None:
            # Use given dimensions, fallback to original if None
            new_size = [
                args.width if args.width is not None else original_size[0],
                args.height if args.height is not None else original_size[1]
            ]
            if len(original_size) > 2:
                new_size.append(args.depth if args.depth is not None else original_size[2])
        elif args.scale is not None:
            new_size = [int(s * args.scale) for s in original_size]
        else:
            raise Exception('Error: You must provide either width/height/depth or scale.')

        # Compute new spacing to preserve physical size
        new_spacing = [
            original_spacing[i] * (original_size[i] / new_size[i]) for i in range(len(new_size))
        ]

        # Map interpolation string to SimpleITK enum
        interp_map = {
            'nearest': sitk.sitkNearestNeighbor,
            'linear': sitk.sitkLinear,
            'bspline': sitk.sitkBSpline,
            'lanczos': sitk.sitkLanczosWindowedSinc,
            'label': sitk.sitkLabelGaussian
        }
        interp = interp_map.get(args.interpolation.lower(), sitk.sitkLinear)

        # Perform resampling
        resampler = sitk.ResampleImageFilter()
        resampler.SetSize(new_size)
        resampler.SetOutputSpacing(new_spacing)
        resampler.SetOutputDirection(inputImage.GetDirection())
        resampler.SetOutputOrigin(inputImage.GetOrigin())
        resampler.SetInterpolator(interp)

        resized_image = resampler.Execute(inputImage)

        sitk.WriteImage(resized_image, str(args.output_image))
