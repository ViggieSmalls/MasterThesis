import numpy as np
import mrcfile
import os


def frequencies(array):
    """
    Creates a frequency map for a multidimensional numpy array with the same dimensions.
    The frequency units are in spacial frequency units. (i.e. nyquist = 0.5)
    """
    meshgrids = np.meshgrid(*[np.fft.fftfreq(i) for i in array.shape], indexing='ij')
    return np.sqrt(np.sum([i**2 for i in meshgrids], axis=0))

def damage_filter(k, N):
    """
    Dose dependent frequency filter.
    Grant, Timothy and Grigorieff, Nikolaus: Measuring the optimal exposure for single particle cryo-EM using a 2.6 Å reconstruction of rotavirus VP6
    :param k: spacial frequency in 1/A
    :param N: cumulative electron exposure in e/A²
    :return: attenuated frequency
    """
    return np.exp(-N / (2 * (0.245 * np.power(k, -1.665) + 2.81)))

def main(map_in, output_dir, voxel_size, dose, n_frames, factor):

    # determine the electron dose at which we have to filter
    dose_per_frame = dose / n_frames
    dose_array = np.append(0, np.cumsum(np.repeat(dose_per_frame, n_frames-1)))

    print('Input map:', map_in)
    print('Output folder:', os.path.abspath(output_dir))
    print('Voxel size of the map:', voxel_size)
    print('Dose array:', dose_array)
    print('Factor:', factor)

    if input('Do you wish to proceed with these values?\n') not in ('y', 'yes'):
        return

    os.makedirs(output_dir, exist_ok=True)

    # open map an fourier transform it
    mrc = mrcfile.open(map_in, permissive=True)
    background_potential = mrc.data.min()
    # set background values to 0
    ary = mrc.data - background_potential
    # apply padding to not cot through filtered result
    padded_map = np.pad(ary, 10, 'constant', constant_values=0)
    # lower the scattering potential to match the particle intensity in real images
    padded_map /= factor
    # fourier transform the image to apply damage filter
    ft_padded_map = np.fft.fftn(padded_map)
    # get frequencies in unit 1/A to create the filter
    freq = frequencies(padded_map)
    freq_A = freq / voxel_size


    for N in dose_array:
        output_map_name = os.path.join(output_dir, "filt_{:5.3f}.mrc".format(N))
        # create frequency mask
        frequency_mask = damage_filter(freq_A, N)
        # attenuate the fourier frequencies of the map
        filtered_map = np.real(np.fft.ifftn(ft_padded_map * frequency_mask))
        # add back the background potential to the map
        filtered_map += background_potential

        with mrcfile.new(output_map_name, overwrite=True) as new_mrc:
            new_mrc.set_data(filtered_map.astype(np.float32))
            new_mrc.flush()
        print("Created damage filtered map with a cumulative dose of {:5.3f} e/A²".format(N))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create TEM-Simulator input files.')
    parser.add_argument('input_map', type=str,
                        help='Input density map (.mrc)')
    parser.add_argument('output_dir', type=str,
                        default=os.path.join(os.path.abspath(os.curdir), 'filtered_maps'),
                        help='Output directory for the input files')
    parser.add_argument('--voxelsize', type=float, default=1.0,
                        help='Voxel size of the map in Angstrom')
    parser.add_argument('--dose', type=float, default=30,
                        help='Total electron dose for micrograph, in e/A²')
    parser.add_argument('-nf','--n_frames', type=int, default=1,
                        help='Number of frames')
    parser.add_argument('--factor', type=float, default=1,
                        help='Reduce the intensity of the scattering potential by this factor')


    args = parser.parse_args()

    main(map_in=args.input_map,
         output_dir=args.output_dir,
         voxel_size=args.voxelsize,
         dose=args.dose,
         n_frames=args.n_frames,
         factor=args.factor)
