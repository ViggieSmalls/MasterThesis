import numpy as np
import mrcfile

def main(args):
    output = "flat_noise.mrc"

    ary = np.ones((1,args.shape[1],args.shape[0])) * args.x
    ary = np.pad(ary, 1, 'constant', constant_values=0)

    with mrcfile.new(output, overwrite=True) as new_mrc:
        new_mrc.set_data(ary.astype(np.float32))
        new_mrc.flush()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create an mrc file with a constant value specified by the provided argument and padded with zeros.')
    parser.add_argument('x', type=int, help='Noise level')
    parser.add_argument('--shape', type=int, nargs=2, default=(5200,5200),
                        help='Shape of the output mrc file (no borders). (default = 5200 x 5200)')
    args = parser.parse_args()
    main(args)

