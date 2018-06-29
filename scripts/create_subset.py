#! /fs/mpib/pool-apps-rzg/system/SLES12/soft/python/anaconda/3/4.2.0/bin/python

import pandas as pd
import random

def relion_star_file_to_DataFrame(path):
    cnt = 0
    df_columns = []

    with open(path) as star_file:
        for line in star_file:
            stripped_line = line.strip()
            if stripped_line.startswith("data_") or stripped_line.startswith("loop_") or stripped_line == "":
                cnt += 1
            elif stripped_line.startswith("_"):
                df_columns.append(stripped_line.split()[0])
                cnt += 1
            else:
                break
        star_file.close()

    return pd.read_csv(path, skiprows=cnt, delim_whitespace=True, names=df_columns)

def pandas_DataFrame_to_relion_star_file(df, out_star):
    with open(out_star, 'w') as f:
        f.write('data_\nloop_\n')
        rln_cols = []
        for col in df.columns:
            if col.startswith('_rln'):
                f.write(col + '\n')
                rln_cols.append(col)
        df[rln_cols].to_csv(f, header=False, index=False, sep='\t')

def get_particle_subset(relion_star_file, k):
    df = relion_star_file_to_DataFrame(relion_star_file)
    subset = df.iloc[random.sample(range(len(df)), k=k)]
    return subset


def main(input_file, output_file, n):
    subset = get_particle_subset(input_file, n)
    pandas_DataFrame_to_relion_star_file(subset, output_file)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create subsets from an input particles.star file.')
    parser.add_argument('-i', '--input_file', type=str,  # how do I only use -i?
                        help='Input particles.star file')
    parser.add_argument('-o', '--output_file', type=str,
                        help='Output subset star file')
    parser.add_argument('-n', '--size', type=int,
                        help='Size of the output subset')

    args = parser.parse_args()

    main(args.input_file, args.output_file, args.size)
