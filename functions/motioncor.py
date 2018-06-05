import numpy as np
import re
import pandas as pd
import os

def get_shifts(motioncor_log, apix):
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

path = '/home/victor/MasterThesis/drift/real_drift/'

for i in range(5):
    mcor_log = '{:02d}.log'.format(i)
    # drift_file = 'drift_{:03d}.txt'.format(i)
    shifts = get_shifts(os.path.join(path,mcor_log), 1.06)
    # drift = pd.read_table(os.path.join(path, drift_file), names='x y'.split())
    shifts.to_csv(os.path.join(path, 'plot{:02d}.csv'.format(i)), index=False)
    # drift.to_csv(os.path.join(path, 'shifts_true_defocus.csv'), index=False)
    # x_err = drift['x'] + shifts['x']
    # y_err = drift['y'] + shifts['y']
    # err = np.sqrt(x_err**2 + y_err**2)
    # print(err.sum())
