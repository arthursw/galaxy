class Tool:

    name = "Extract channel"
    description = "Extract an image channel."
    categories = ['Basics']
    inputs = [
            dict(
            name = 'input_image',
            help = 'Input image',
            type = 'Path',
            required = True,
            autoColumn = True,
        ),
        dict(
            name = 'channel',
            help = 'Channel to extract',
            type = 'int',
            default = 0,
        ),
    ]
    outputs = [
        dict(
            name = 'output_image',
            help = 'Output image',
            default = '{input_image.stem}_{channel}.ome.tif',
            type = 'Path',
        ),
    ]

    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        from bioio import BioImage
        from bioio.writers import OmeTiffWriter
        image = BioImage(args.input_image)
        channel = image.get_image_data("TCZYX", C=args.channel)
        OmeTiffWriter.save(channel, args.output_image, dim_order="TCZYX")