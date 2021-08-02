""" Utility to calculate statistics in a single pass """
import numpy as np

# Python implementation of Welford's online algorithm
# Inspired by http://www.johndcook.com/standard_deviation.html
def get_std_err(xs, ms, n, std_err=None, m=None, s=None):
    """
    Calculate the std err
    Arguments:
    xs: raw data matrix, xs.shape[0] is the repetition dimension, while xs.shape[1] is the sweep dimension.
    ms: mean value
    n: the repetition = xs.shape[0]
    std_err: previous std err
    m: previous mean value
    s: previous sum of squares of differences fro mthe current mean
    """
    if std_err is None:  
        old_m, old_s = xs[0], np.zeros(xs.shape[1])  # m_1 = x_1, s_1 = 0
        xs, ms = xs[1:], ms[1:]  # safe to ignore first result array
    else:
        old_m, old_s = m, s  # recall m_k-1, s_k-1
    # s_k = s_k-1 + (x_k - m_k-1) * (x_k - m_k)
    new_deltas, old_deltas = xs - ms, xs - np.insert(ms, 0, old_m, 0)[:-1]
    new_ss = np.vstack(((new_deltas * old_deltas), old_s))
    new_m, new_s = ms[-1], np.sum(new_ss, axis=0)
    std_err = np.sqrt(new_s / (n * (n - 1)))
    return std_err, new_m, new_s

"""# test by generating random data
import scipy.stats as sps
import random

rows, cols = 20000, 10
xs_ = np.random.normal(5e-7, 2.5e-7, size=(rows, cols))
ms_ = np.zeros((rows, cols))
for i in range(rows):
    ms_[i] = np.average(xs_[:i+1], axis=0)

print("get_std_err()...")
stats = tuple()
start = 4
stats = get_std_err(xs_[:start], ms_[:start], start)
for i in range(start + 1, rows, random.randint(2, 100)):
    stats = get_std_err(xs_[start:i], ms_[start:i], i+1, *stats)
    start = i

print(f"stderr: {stats[0]}")
print()
print("scipy...")
print(sps.sem(xs_, axis=0))"""
