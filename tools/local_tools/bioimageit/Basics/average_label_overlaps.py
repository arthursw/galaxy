import pandas

class Tool():

    name = "Count label overlaps"
    description = "Count the number (or average number) of overlapping labels. For example: 3 label2 on label1 number 1, 4 label2 on label1 number 2, etc. If average is true, the average number of label2 per label1 is returned."
    categories = ['SimpleITK']
    inputs = [
        dict(
            name = 'label1_min',
            help = 'The minimum value of label1 to keep. Ignored if None (None by default).',
            type = 'float',
            default = None,
        ),
        dict(
            name = 'label1_max',
            help = 'The maximum value of label1 to keep. Ignored if None (None by default).',
            type = 'float',
            default = None,
        ),
        dict(
            name = 'average',
            help = 'Compute average number of label2 per label1 instead of number of label2 by label1',
            type = 'bool',
            default = False,
        ),]
    outputs = []
    
    def processDataFrame(self, dataFrame, argsList):
        args = argsList[0]
        if args.label1_min is not None:
            dataFrame = dataFrame[dataFrame['label1']>=args.label1_min]
        if args.label1_max is not None:
            dataFrame = dataFrame[dataFrame['label1']<=args.label1_max]
        if 'label1' not in dataFrame.columns: return pandas.DataFrame()
        result = dataFrame.groupby(['image1','label1'])['label2'].agg(lambda x: (x != 0).sum()).reset_index(name="label2_count")
        if args.average:
            return result.groupby('image1')['label2_count'].mean().reset_index(name='average_number_of_label2_per_label1')
        else:
            return result