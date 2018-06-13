import re
import numpy as np
import pandas as pd

def read_motioncor_log(motioncor_log):
    """
    reads the motioncor log file and returns the values for the frame shifts in pixels.
    :param motioncor_log: path to motioncor log file
    :return: Dictionary with x and y shift values for every frame
    """
    with open(motioncor_log) as logfile:
        l = [i for i in logfile.readlines() if i.startswith("...... Frame ")]

    l = [re.findall("[-+]?\d*\.\d+", i) for i in l]

    x = [float(i[0]) for i in l]
    y = [float(i[1]) for i in l]

    return {'x': x, 'y': y}

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