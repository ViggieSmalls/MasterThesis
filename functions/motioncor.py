import numpy as np
import re
import pandas as pd


def plot_shift(motioncor_log, apix):
    """
    returns the frame shift in nm
    :param motioncor_log:
    :param apix:
    :return:
    """
    with open(motioncor_log) as logfile:
        l = [i for i in logfile.readlines() if i.startswith("...... Frame ")]

    # get x and y translation
    _l = [re.findall("[-+]?\d*\.\d+", i) for i in l]
    np_l = np.array(_l).astype(np.float)

    # x = np.cumsum(np_l[:,0]) * apix /10
    # y = np.cumsum(np_l[:,1]) * apix /10
    x = np_l[:,0] * apix /10
    y = np_l[:,1] * apix /10

    data = pd.DataFrame(data={'x': x, 'y': y})
    return data