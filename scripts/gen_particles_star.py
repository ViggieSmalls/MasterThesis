import numpy as np
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

def main(args):

    df = pd.DataFrame()

    defocus_values = np.random.uniform(args.defocus[0], args.defocus[1], args.mics)
    if args.ps != (None, None):
        phase_shift_values = np.linspace(args.ps[0], args.ps[1], args.mics)
    elif args.ps == (None, None):
        phase_shift_values = np.repeat(None, args.mics)

    det_pix_x = 3838
    det_pix_y = 3710

    if args.angles:
        angles_df = relion_star_file_to_DataFrame(args.angles)

    for micrograph, defocus, ps in zip(range(args.mics), defocus_values, phase_shift_values):
        mic_df = pd.DataFrame()
        nx = np.linspace(-((args.np[1] - 1) * args.pd / 2), ((args.np[1] - 1) * args.pd / 2), args.np[1])
        ny = np.linspace(-((args.np[0] - 1) * args.pd / 2), ((args.np[0] - 1) * args.pd / 2), args.np[0])
        x = np.repeat(nx, args.np[0])
        y = np.tile(ny, args.np[1])

        # change relion coordinates
        mic_df['_rlnCoordinateX'] = np.round(x * 10 / args.apix + det_pix_x // 2).astype(int)
        mic_df['_rlnCoordinateY'] = np.round(y * 10 / args.apix + det_pix_y // 2).astype(int)

        if args.angles:
            # angles_df = relion_star_file_to_DataFrame(args.angles)
            start = int(micrograph) * len(x)
            subset = angles_df.iloc[np.arange(start, start+len(x))]
            mic_df['_rlnAnglePsi'] = np.round(subset['_rlnAnglePsi'].values, 2)
            mic_df['_rlnAngleTilt'] = np.round(subset['_rlnAngleTilt'].values, 2)
            mic_df['_rlnAngleRot'] = np.round(subset['_rlnAngleRot'].values, 2)
        elif args.angles is None:
            mic_df['_rlnAnglePsi'] = np.random.uniform(args.psi[0], args.psi[1], len(x))
            mic_df['_rlnAngleTilt'] = np.random.uniform(args.tilt[0], args.tilt[1], len(x))
            mic_df['_rlnAngleRot'] = np.random.uniform(args.rot[0], args.rot[1], len(x))

        mic_df['_rlnDefocusU'] = defocus*10000  # Angstrom
        mic_df['_rlnDefocusV'] = defocus*10000  # Angstrom
        mic_df['_rlnDefocusAngle'] = 0
        if ps is not None:
            mic_df['_rlnPhaseShift'] = ps
        mic_df['_rlnMagnification'] = 10000
        mic_df['_rlnDetectorPixelSize'] = args.apix
        mic_df['_rlnMicrographName'] = 'micrograph_{:03d}.mrc'.format(micrograph)

        df = df.append(mic_df)

    pandas_DataFrame_to_relion_star_file(df, args.file)



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create a star file for `gen_temsim_input_files.py`. '
                                                 'Particles are positioned on a grid at a specified distance (default=10 nm). '
                                                 'You can specify the number of micrographs, defocus and phase shift. ')
    parser.add_argument('file', type=str,
                        help='File name of output particles star file.')
    parser.add_argument('--rot', type=float, nargs=2, default=(0,360),  #FIXME check the default range for relion
                        help='Min and max values of randomly generated angles. (default = 0 to 360)')
    parser.add_argument('--tilt', type=float, nargs=2, default=(0,360),  #FIXME check the default range for relion
                        help='Min and max values of randomly generated angles. (default = 0 to 360)')
    parser.add_argument('--psi', type=float, nargs=2, default=(-180,180),  # this range is correct
                        help='Min and max values of randomly generated angles. (default = -180 to 180)')
    parser.add_argument('--angles', type=str, default=None,
                        help='particles.star file from which samples of euler angles are drawn')
    parser.add_argument('--pd', type=float, default=10,
                        help='Distance between particle centers in nanometer.')
    parser.add_argument('--np', type=int, nargs=2, default=(2, 2),
                        help='Number of particles per row (first argument) and column (second argument).')
    parser.add_argument('--mics', type=int, default=1,
                        help='Number of micrographs.')
    parser.add_argument('--apix', type=float, default=1,
                        help='Pixel size of the output micrograph.')
    parser.add_argument('--defocus', type=float, nargs=2, default=(0, 1),
                        help='Lower and upper defocus limit in micrometer. Values are uniformly distributed.')
    parser.add_argument('--ps', type=float, nargs=2, default=(None, None),
                        help='Lower and upper phase shift in degrees. Values are increasing from low to high. (default = no phase shift)')
    args = parser.parse_args()

    main(args)