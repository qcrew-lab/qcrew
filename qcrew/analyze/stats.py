""" """

import numpy as np

# def get_std_err(xs, ms, n, std_err=None, m=None, s=None):
#     """
#     Python implementation of Welford's online algorithm to calculate running std err
#     Inspired by http://www.johndcook.com/standard_deviation.html
#     Arguments:
#     xs: raw data matrix, xs.shape[0] is the repetition dimension, while xs.shape[1] is the sweep dimension.
#     ms: mean value
#     n: the repetition = xs.shape[0]
#     std_err: previous standard deviaiton error
#     m: previous mean value
#     s: previous sum of squares of differences from the current mean
#     """
#     if std_err is None:
#         old_m, old_s = xs[0], np.zeros(xs.shape[1])  # m_1 = x_1, s_1 = 0
#         xs, ms = xs[1:], ms[1:]  # safe to ignore first result array
#     else:
#         old_m, old_s = m, s  # recall m_k-1, s_k-1

#     # the following lines do s_k = s_k-1 + (x_k - m_k-1) * (x_k - m_k)
#     new_deltas, old_deltas = xs - ms, xs - np.insert(ms, 0, old_m, 0)[:-1]
#     new_ss = np.vstack(((new_deltas * old_deltas), old_s))
#     new_m, new_s = ms[-1], np.sum(new_ss, axis=0)
#     std_err = np.sqrt(new_s / (n * (n - 1)))
#     return std_err, new_m, new_s


def get_std_err(data_mtx, mean_mtx, n, std_err=None, mean=None, sum_sq_diff=None):
    """Python implementation of Welford's online algorithm to calculate running standard deviation.
       We assume that there is a complete data matrix which we want to calcuate the standard deviaiton
       over its first dimension. However, we only can get a partial part of this complete data matrix
       and the incremental average matrix over the previous data in each time. This method calcuate the
       running standard deviation based on updated partial data ``data_mtx``, updated mean value ``mean_mtx``,
       last mean value ``mean`` and last sum of square of difference from last mean value ``sum_sq_diff``.

       Inspired by http://www.johndcook.com/standard_deviation.html

    Args:
        data_mtx (np.ndarry): updated partial data matrix with at least 2 dimensions, in which
                              the standard deviation error will be calcualted over the first dimension.
        mean_mtx (np.ndarry): updated mean value matrix with the same shape as data_mtx, of which each
                              element is the mean value of the previous data over the first dimension
        n (int): the latest index of partial data matrix
        std_err: last standard deviation
        mean: last mean value
        sum_sq_diff: last sum of square of difference from the mean value
    """
    # the first calculation
    if std_err is None:
        # old mean value is set as the first column
        # old sum is set as zero
        old_mean, old_sum_sq_diff = data_mtx[0], np.zeros(data_mtx.shape[1:])

        # remove the first column
        data_mtx, mean_mtx = data_mtx[1:], mean_mtx[1:]

    else:
        old_mean, old_sum_sq_diff = mean, sum_sq_diff

    # the following lines do s_k = s_k-1 + (x_k - m_k-1) * (x_k - m_k)
    new_deltas = data_mtx - mean_mtx
    old_deltas = data_mtx - np.insert(data_mtx, 0, old_mean, 0)[:-1]
    new_ss = np.vstack(((new_deltas * old_deltas), old_sum_sq_diff))

    new_mean, new_sum = mean_mtx[-1], np.sum(new_ss, axis=0)
    std_err = np.sqrt(new_sum / (n * (n - 1)))
    return std_err, new_mean, new_sum
