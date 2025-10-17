import argparse
parser = argparse.ArgumentParser(description="Compute label overlap statistics from two label images.")
parser.add_argument("-l1", "--label1", required=True, help="Input label image 1 path")
parser.add_argument("-l2", "--label2", required=True, help="Input label image 2 path")
parser.add_argument("-o", "--output_csv", required=True, help="Output CSV file with overlap statistics")
argv = ['/Users/amasson/Travail/galaxy/tools/local_tools/custom_label_overlaps/custom_label_overlaps.py', '--label1', '/Users/amasson/Travail/galaxy/database/objects/9/9/c/dataset_99c92653-d4d3-4427-b55b-60b2ce06c490.dat', '--label2', '/Users/amasson/Travail/galaxy/database/objects/2/8/c/dataset_28ccdf60-3571-43a9-b921-70e43b204b86.dat', '--output_csv', '/Users/amasson/Travail/galaxy/database/objects/b/e/e/dataset_beec3c21-7bbf-4a50-bba8-63a6f40bc8cb.dat']
args = parser.parse_args(argv[1:])
print(args.label1)