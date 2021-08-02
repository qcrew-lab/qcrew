""" """

import numpy as np

def get_std_err(xs, ms, n, std_err=None, m=None, s=None):
    """
    Python implementation of Welford's online algorithm to calculate running std err
    Inspired by http://www.johndcook.com/standard_deviation.html
    Arguments:
    xs: raw data matrix, xs.shape[0] is the repetition dimension, while xs.shape[1] is the sweep dimension.
    ms: mean value
    n: the repetition = xs.shape[0]
    std_err: previous std err
    m: previous mean value
    s: previous sum of squares of differences from the current mean
    """
    if std_err is None:
        old_m, old_s = xs[0], np.zeros(xs.shape[1])  # m_1 = x_1, s_1 = 0
        xs, ms = xs[1:], ms[1:]  # safe to ignore first result array
    else:
        old_m, old_s = m, s  # recall m_k-1, s_k-1

    # the following lines do s_k = s_k-1 + (x_k - m_k-1) * (x_k - m_k)
    new_deltas, old_deltas = xs - ms, xs - np.insert(ms, 0, old_m, 0)[:-1]
    new_ss = np.vstack(((new_deltas * old_deltas), old_s))
    new_m, new_s = ms[-1], np.sum(new_ss, axis=0)
    std_err = np.sqrt(new_s / (n * (n - 1)))
    return std_err, new_m, new_s
