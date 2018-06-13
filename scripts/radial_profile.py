##############################################################################################################
# Disables `Unrecognized machine stamp` warning for reading mrc files

import warnings

warnings.simplefilter("ignore")

##############################################################################################################

import pandas as pd
import numpy as np
import mrcfile
import matplotlib.pyplot as plt
import os


def spinavej(x):
    '''
    source: https://github.com/s-sajid-ali/FRC
    '''
    shape = np.shape(x)
    dim = np.size(shape)
    '''
    Depending on the dimension of the image 2D/3D, create an array of integers 
    which increase with distance from the center of the array
    '''
    if dim == 2:
        nr, nc = shape
        nrdc = np.floor(nr / 2) + 1
        ncdc = np.floor(nc / 2) + 1
        r = np.arange(nr) - nrdc + 1
        c = np.arange(nc) - ncdc + 1
        [R, C] = np.meshgrid(r, c)
        index = np.round(np.sqrt(R ** 2 + C ** 2)) + 1

    elif dim == 3:
        nr, nc, nz = shape
        nrdc = np.floor(nr / 2) + 1
        ncdc = np.floor(nc / 2) + 1
        nzdc = np.floor(nz / 2) + 1
        r = np.arange(nr) - nrdc + 1
        c = np.arange(nc) - ncdc + 1
        z = np.arange(nz) - nzdc + 1
        [R, C, Z] = np.meshgrid(r, c, z)
        index = np.round(np.sqrt(R ** 2 + C ** 2 + Z ** 2)) + 1
    else:
        print('input is neither a 2d or 3d array')
    '''
    The index array has integers from 1 to maxindex arranged according to distance
    from the center
    '''
    maxindex = np.max(index)
    output = np.zeros(int(maxindex), dtype=complex)

    '''
    In the next step the output is generated. The output is an array of length
    maxindex. The elements in this array corresponds to the sum of all the elements
    in the original array corresponding to the integer position of the output array 
    divided by the number of elements in the index array with the same value as the
    integer position. 

    Depening on the size of the input array, use either the pixel or index method.
    By-pixel method for large arrays and by-index method for smaller ones.
    '''
    if nr >= 512:
        print('performed by pixel method')
        sumf = np.zeros(int(maxindex), dtype=complex)
        count = np.zeros(int(maxindex), dtype=complex)
        for ri in range(nr):
            for ci in range(nc):
                sumf[int(index[ri, ci]) - 1] = sumf[int(index[ri, ci]) - 1] + x[ri, ci]
                count[int(index[ri, ci]) - 1] = count[int(index[ri, ci]) - 1] + 1
        output = sumf / count
        return output
    else:
        print('performed by index method')
        indices = []
        for i in np.arange(int(maxindex)):
            indices.append(np.where(index == i + 1))
            output[i] = sum(x[indices[i]]) / len(indices[i][0])
        return output


def get_origin_of_patches(shape, patch_size=(512, 512)):
    """
    Divide an image into multiple patches of specified patch size tuple
    :param shape: tuple with image size in pixels
    :param patch_size: tuple patch size in pixels
    :return: list of the origins for the patches
    """
    width, height = shape
    x, y = patch_size

    nx = width // x  # number of patches in x direction
    ny = height // y  # number of patches in y direction
    center = [width // 2, height // 2]  # center of the image

    origin_x = center[0] - nx * x // 2
    origin_y = center[1] - ny * y // 2

    origins = []
    for i in range(nx):
        for j in range(ny):
            origin = (origin_x + x * i, origin_y + y * j)
            origins.append(origin)

    return origins


def PS(path, patch_size=None):
    data = mrcfile.open(path, permissive=True).data
    mean = data.mean()
    image = data.copy() / mean

    if patch_size is None:
        image = image[:min(image.shape), :min(image.shape)]  # crop to square image
        ft = np.fft.fft2(image)
        ps = np.abs(ft) ** 2
    else:
        ps = np.zeros(patch_size)
        origins = get_origin_of_patches(image.shape, patch_size)
        for origin in origins:
            patch = image[origin[0]:origin[0] + patch_size[0], origin[1]:origin[1] + patch_size[1]]
            ft = np.fft.fft2(patch)
            ps += np.abs(ft) ** 2
    return ps


def radp(path, **kwargs):
    ps = PS(path, **kwargs)
    x = np.linspace(0, 0.5, ps.shape[0] // 2)
    rad_avg = spinavej(np.fft.fftshift(ps))
    y = np.real(rad_avg[:len(x)])
    return x, y


def main(images, labels, patch_size, output_csv):
    fig, ax = plt.subplots()

    missing = []

    if os.path.isfile(output_csv):
        df = pd.read_csv(output_csv, delim_whitespace=True)
        for im in images:
            if im + 'x' not in df.columns:
                missing.append(im)
    else:
        missing.extend(images)
        df = pd.DataFrame()

    for im in missing:
        data = {}
        if patch_size < 0:
            x, y = radp(im)
        else:
            x, y = radp(im, patch_size=(patch_size, patch_size))
        data[im + 'x'] = x
        data[im + 'y'] = y
        data = pd.DataFrame(data)
        df = pd.concat([df, data], axis=1)
        # df = df.append(data)
        df.to_csv(output_csv, index=False, sep='\t')

    df = pd.read_csv(output_csv, delim_whitespace=True)
    for n, im in enumerate(images):
        x = df[im + 'x']
        y = df[im + 'y']
        ax.semilogy(x, y, label=im if labels is None else labels[n])

    ax.legend()
    plt.show()


if __name__ == '__main__':

    import argparse
    from glob import glob

    parser = argparse.ArgumentParser(description='Create radial profiles of power spectra for input micrographs.')
    parser.add_argument('micrographs', type=str, nargs='+',
                        help='Input micrographs (mrc file format)')
    parser.add_argument('--labels', type=str, nargs='+',
                        help='Labels for the output plot.')
    parser.add_argument('--patch', type=int, default=512,
                        help='Patch size for computing the power spectrum. Use negative values to not use patches.')
    parser.add_argument('--csv', type=str, default="profiles.csv",
                        help='Name of the csv file containing the results. If file already exists, it is read, so radial profiles do not need to be calculated twice.')
    args = parser.parse_args()

    files = set()
    for pattern in args.micrographs:
        files.update(glob(pattern))

    main(files, args.labels, args.patch, args.csv)
