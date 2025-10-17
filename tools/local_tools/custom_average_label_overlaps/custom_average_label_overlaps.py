import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Count the number (or average) of overlapping labels.")
    parser.add_argument("--input_csv", required=True, help="Input CSV (from label_overlaps tool)")
    parser.add_argument("--output_csv", required=True, help="Output CSV file")
    parser.add_argument("--label1_min", type=float, default=None, help="Minimum label1 to keep (None = no minimum)")
    parser.add_argument("--label1_max", type=float, default=None, help="Maximum label1 to keep (None = no maximum)")
    parser.add_argument("--average", action="store_true", help="Compute average number of label2 per label1 instead of counts per label1")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)

    if 'label1' not in df.columns or 'label2' not in df.columns:
        pd.DataFrame().to_csv(args.output_csv, index=False)
        return

    if args.label1_min is not None:
        df = df[df['label1'] >= args.label1_min]
    if args.label1_max is not None:
        df = df[df['label1'] <= args.label1_max]

    # count number of nonzero label2 per label1
    result = df.groupby(['image1', 'label1'])['label2'].agg(lambda x: (x != 0).sum()).reset_index(name="label2_count")

    if args.average:
        result = result.groupby('image1')['label2_count'].mean().reset_index(name='average_number_of_label2_per_label1')

    result.to_csv(args.output_csv, index=False)

if __name__ == "__main__":
    main()
