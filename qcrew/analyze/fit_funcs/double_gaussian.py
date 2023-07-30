import numpy as np


def func(xs, x0, x1, a0, a1, ofs, sigma=2):
    """
    Gaussian defined by it's area <area>, sigma <s>, position <x0> and
    y-offset <ofs>.
    """
    r0 = (xs - x0) ** 2
    r1 = (xs - x1) ** 2
    ys = ofs + a0 * np.exp(-0.5 * r0 / sigma ** 2) + a1 * np.exp(-0.5 * r1 / sigma ** 2)
    return ys


def guess(xs, ys, zs):
    print("ERROR: guess function not implemented. Provide your own guess.")
    return dict()
