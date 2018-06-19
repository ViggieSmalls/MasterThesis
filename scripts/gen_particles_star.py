import numpy as np
import pandas as pd

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
    phase_shift_values = np.linspace(args.ps[0], args.ps[1], args.mics)

    det_pix_x = 3838
    det_pix_y = 3710

    for micrograph, defocus, ps in zip(range(args.mics), defocus_values, phase_shift_values):
        mic_df = pd.DataFrame()
        nx = np.linspace(-((args.np[1] - 1) * args.pd / 2), ((args.np[1] - 1) * args.pd / 2), args.np[1])
        ny = np.linspace(-((args.np[0] - 1) * args.pd / 2), ((args.np[0] - 1) * args.pd / 2), args.np[0])
        x = np.repeat(nx, args.np[0])
        y = np.tile(ny, args.np[1])

        # change relion coordinates
        mic_df['_rlnCoordinateX'] = np.round(x * 10 / args.apix + det_pix_x // 2).astype(int)
        mic_df['_rlnCoordinateY'] = np.round(y * 10 / args.apix + det_pix_y // 2).astype(int)
        mic_df['_rlnAnglePsi'] = np.random.uniform(args.psi[0], args.psi[1], len(x))
        mic_df['_rlnAngleTilt'] = np.random.uniform(args.tilt[0], args.tilt[1], len(x))
        mic_df['_rlnAngleRot'] = np.random.uniform(args.rot[0], args.rot[1], len(x))

        mic_df['_rlnDefocusU'] = defocus*10000  # Angstrom
        mic_df['_rlnDefocusV'] = defocus*10000  # Angstrom
        mic_df['_rlnDefocusAngle'] = 0
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
                        help='File name of autput particles star file.')
    parser.add_argument('--rot', type=float, nargs=2, default=(0,360),  #FIXME check the default range for relion
                        help='Min and max values of randomly generated angles. (default = 0 to 360)')
    parser.add_argument('--tilt', type=float, nargs=2, default=(0,360),  #FIXME check the default range for relion
                        help='Min and max values of randomly generated angles. (default = 0 to 360)')
    parser.add_argument('--psi', type=float, nargs=2, default=(-180,180),  # this range is correct
                        help='Min and max values of randomly generated angles. (default = -180 to 180)')
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
    parser.add_argument('--ps', type=float, nargs=2, default=(36, 144),
                        help='Lower and upper phase shift in degrees. Values are increasing from low to high. (default = 36 to 144)')
    args = parser.parse_args()

    main(args)