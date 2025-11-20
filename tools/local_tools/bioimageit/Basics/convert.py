class Tool:

    name = "Convert Image BioIO"
    description = "Read and write an image with BioIO."
    categories = ['Basics']
    inputs = [
            dict(
            name = 'input_image',
            help = 'Input image',
            type = 'Path',
            required = True,
            autoColumn = True,
        ),
    ]
    outputs = [
        dict(
            name = 'output_image',
            help = 'Output image',
            default = '{input_image.stem}.ome.tif',
            type = 'Path',
        ),
    ]

    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        from bioio import BioImage
        from bioio.writers import OmeTiffWriter
        image = BioImage(args.input_image)
        OmeTiffWriter.save(image.data, args.output_image, dim_order="TCZYX")