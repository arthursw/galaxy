class Tool():
    
    name = "ZProjection"
    description = "Project the Z axis using min intensity, max intensity, average intensity, sum, standard deviation, median."
    categories = ['Basics']

    inputs = [dict(name='input_image', help='The input image path.', 
                   required=True, type='Path', autoColumn=True),
                dict(name='channel', help='The channel to extract.', 
                   required=True, type='int', default=2),
                dict(name='projection_type', help='The projection type.', 
                   required=True, type='str', choices=["Max", "Min", "Average", "Sum", "Standard deviation", "Median"]),]
    
    outputs = [dict(name='output_image', help='The output image.', 
                    default='{input_image.astem}.ome.tif', type='Path')]
    
    def processData(self, args):
        from bioio import BioImage
        from bioio.writers import OmeTiffWriter
        import numpy as np
        image = BioImage(args.input_image)
        if args.projection_type == "Max":
            result = image.data.max(axis=args.channel)
        elif args.projection_type == "Min":
            result = image.data.min(axis=args.channel)
        if args.projection_type == "Average":
            result = image.data.mean(axis=args.channel)
        if args.projection_type == "Sum":
            result = image.data.sum(axis=args.channel)
        if args.projection_type == "Standard deviation":
            result = image.data.std(axis=args.channel)
        if args.projection_type == "Median":
            result = np.median(image.data, axis=args.channel)
        OmeTiffWriter.save(result, args.output_image, dim_order="TCYX")
    

