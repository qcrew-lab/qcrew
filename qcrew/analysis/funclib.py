""" """

from typing import Any

import numpy as np

func_map = {"constant": constant_fn, "gaussian": gaussian_fn}


def constant_fn(x: Any) -> Any:
    """ """
    return x


def gaussian_fn(maximum: float, sigma: float, multiple_of_sigma: int) -> np.ndarray:
    """ """
    length = int(multiple_of_sigma * sigma)
    mu = int(np.floor(length / 2))
    t = np.linspace(0, length - 1, length)
    gaussian = maximum * np.exp(-((t - mu) ** 2) / (2 * sigma ** 2))
    return [float(x) for x in gaussian]
