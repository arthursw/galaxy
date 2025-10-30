#!/usr/bin/env python3
import sys
import argparse

def merge_files(output_path, inputs):
    first_header = None
    wrote_any = False

    with open(output_path, "w", newline="") as out_f:
        for idx, fp in enumerate(inputs):
            try:
                with open(fp, "r", newline="") as in_f:
                    # read first line as header (or empty if file empty)
                    first_line = in_f.readline()
                    if first_line == "":
                        # empty file -> skip
                        print(f"Warning: skipping empty file {fp}", file=sys.stderr)
                        continue

                    # normalize newline and remove trailing newline
                    header = first_line.rstrip("\r\n")

                    if first_header is None:
                        first_header = header
                        # write header + rest of file
                        out_f.write(header + "\n")
                        # write rest of file
                        for line in in_f:
                            out_f.write(line)
                        wrote_any = True
                    else:
                        if header == first_header:
                            # skip header, write rest
                            for line in in_f:
                                out_f.write(line)
                        else:
                            # header differs: warn and append full file (including its header)
                            print(f"Warning: header differs in {fp}; appending full file.", file=sys.stderr)
                            out_f.write(header + "\n")
                            for line in in_f:
                                out_f.write(line)
                            wrote_any = True
            except Exception as e:
                print(f"Error reading {fp}: {e}", file=sys.stderr)
                raise

    if not wrote_any:
        # ensure we still create an empty output if nothing was written
        open(output_path, "a").close()

def main():
    parser = argparse.ArgumentParser(description="Merge CSV inputs into a single CSV. Keeps only the first header line if headers match.")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file path")
    parser.add_argument("inputs", nargs="+", help="Input CSV files")
    args = parser.parse_args()
    merge_files(args.output, args.inputs)

import sys

def __galaxy_entry_point__(args):
    sys.argv = args
    main()

if __name__ == "__main__":
    __galaxy_entry_point__(sys.argv)

