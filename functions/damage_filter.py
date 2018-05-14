import numpy as np

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

