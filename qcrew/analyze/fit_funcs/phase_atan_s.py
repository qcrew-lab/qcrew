import numpy as np


def func(xs, fr, Q, ofs):
    """
    xs: array of probe frequencies
    ofs: arbitrary y phase offset
    fr: resonance frequency
    """
    return ofs + 2 * np.arctan(2 * Q * (xs / fr - 1))


def guess(xs, ys):
    fr = xs[np.argmax(np.gradient(ys))]
    Q = (fr / (np.max(xs) - np.min(xs))) * np.sqrt(len(xs))
    ofs = (np.average(ys[:5]) + np.average(ys[-5:])) / 2
    return {"fr": fr, "Q": Q, "ofs": ofs}
