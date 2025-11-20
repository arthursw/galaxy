import numbers
import pandas

class Tool:

    name = "Filter out rows"
    description = "Filter out rows containing given values and from given range."
    categories = ['DataFrame']

    inputs = [
        dict(
            required = True,
            name = 'column_name',
            help = 'Column name',
            type = 'str',
            autoColumn = False,
        ),
        dict(
            name = 'min',
            help = 'The minimum value to keep. Ignored if None (None by default).',
            type = 'float',
            default = None,
        ),
        dict(
            name = 'max',
            help = 'The maximum value to keep. Ignored if None (None by default).',
            type = 'float',
            default = None,
        ),
        dict(
            name = 'numbers_to_remove',
            help = 'Comma separated numbers to filter out (for example "0,1,55").',
            type = 'str',
            default = '',
        ),
        dict(
            name = 'strings_to_remove',
            help = 'Comma separated string to filter out (for example "the,words,to,remove").',
            type = 'str',
            default = '',
        ),
    ]
    outputs = [
    ]
    
    def num(self, s):
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return None
    
    def parseValues(self, values):
        return values.replace('[', '').replace(']', '').split(',')
    
    def parseNumbers(self, values):
        result = [self.num(v) for v in self.parseValues(values)]
        return [v for v in result if isinstance(v, numbers.Number)]
    
    def processDataFrame(self, dataFrame: pandas.DataFrame, argsList):
        args = argsList[0]
        if args.min is not None:
            dataFrame = dataFrame[dataFrame[args.column_name]>=args.min]
        if args.max is not None:
            dataFrame = dataFrame[dataFrame[args.column_name]<=args.max]
        if args.numbers_to_remove is not None:
            numbers_to_remove = self.parseNumbers(args.numbers_to_remove)
            dataFrame = dataFrame[~dataFrame[args.column_name].isin(numbers_to_remove)]
        if args.strings_to_remove is not None:
            strings_to_remove = self.parseValues(args.strings_to_remove)
            dataFrame = dataFrame[~dataFrame[args.column_name].isin(strings_to_remove)]
        return dataFrame