""" """

from numbers import Real
from typing import ClassVar

import numpy as np

from qcrew.helpers.parametrizer import Parametrized

from qcrew.control.instruments.quantum_machines import DEFAULT_AMP


class Wave(Parametrized):
    """ """

    _parameters: ClassVar[set[str]] = set()  # subclasses to override

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}({self.parameters})"

    def __call__(self, *args: Real) -> np.ndarray:
        """ """
        raise NotImplementedError  # subclasses must implement

    @property  # waveform type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "arbitrary"


class ConstantWave(Wave):
    """ """

    _parameters: ClassVar[set[str]] = {"ampx", "length"}

    def __init__(self, ampx: float, length: int = None) -> None:
        """ """
        self.ampx: float = ampx
        self.length: int = length

    def __call__(self, ampx: float, length: int) -> np.ndarray:
        """ """
        return np.full(length, (DEFAULT_AMP * ampx))

    @property  # waveform type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "constant"


class GaussianWave(Wave):
    """ """

    _parameters: ClassVar[set[str]] = {"ampx", "sigma", "chop"}

    def __init__(self, ampx: float, sigma: int, chop: int) -> None:
        """ """
        self.ampx: float = ampx
        self.sigma: int = sigma
        self.chop: int = chop

    def __call__(self, ampx: float, sigma: int, chop: int) -> np.ndarray:
        """ """
        ts = np.linspace(-chop / 2 * sigma, chop / 2 * sigma, chop * sigma)
        return DEFAULT_AMP * ampx * np.exp(-(ts ** 2) / (2.0 * sigma ** 2))


class GaussianDragWave(Wave):
    """ """

    _parameters: ClassVar[set[str]] = {"drag", "sigma", "chop"}

    def __init__(self, drag: float, sigma: int, chop: int) -> None:
        """ """
        self.drag: float = drag
        self.sigma: int = sigma
        self.chop: int = chop

    def __call__(self, drag: float, sigma: int, chop: int) -> np.ndarray:
        """ """
        ts = np.linspace(-chop / 2 * sigma, chop / 2 * sigma, chop * sigma)
        return drag * (0.25 / sigma ** 2) * ts * np.exp(-(ts ** 2) / (2.0 * sigma ** 2))
        # NOTE where did the 0.25 come from???


class CosRampWave(Wave):
    """ """

    _parameters: ClassVar[set[str]] = {"length", "ampx", "flip"}

    def __init__(self, length: int, ampx: float, flip: bool = False) -> None:
        """ """
        self.length: int = length
        self.ampx: float = ampx
        self.flip: bool = flip

    def __call__(self, length: int, ampx: float, flip: bool = False) -> np.ndarray:
        """ """
        samples = DEFAULT_AMP * ampx * 0.5 * (1 - np.cos(np.linspace(0, np.pi, length)))
        if flip:
            return samples[::-1]
        return samples
        # NOTE should be always start ramp from/to 0.0 or should that be settable?
        # NOTE amp is the amp you ramp up to from 0.


class TanhRampWave(Wave):
    """ """

    _parameters: ClassVar[set[str]] = {"length", "ampx", "flip"}

    def __init__(self, length: int, ampx: float, flip: bool = False) -> None:
        """ """
        self.length: int = length
        self.ampx: float = ampx
        self.flip: bool = flip

    def __call__(self, length: int, ampx: float, flip: bool = False) -> np.ndarray:
        """ """
        samples = DEFAULT_AMP * ampx * 0.5 * (1 + np.tanh(np.linspace(-2, 2, length)))
        if flip:
            return samples[::-1]
        return samples
        # NOTE with this fn, we ramp up very close to, but not exactly at amp
        # NOTE perhaps we can add a start y offset so we end exactly at amp?


class IntegrationWeight(Parametrized):
    """ """

    _parameters: ClassVar[set[str]] = {"cos", "sin", "length"}

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}({self.parameters})"

    def __call__(self, *args: Real) -> tuple[np.ndarray]:
        """ """
        raise NotImplementedError  # subclasses must implement


class ConstantIntegrationWeight(IntegrationWeight):
    """ """

    _parameters: ClassVar[set[str]] = {"cos", "sin", "length"}

    def __init__(self, cos: float, sin: float, length: int) -> None:
        """ """
        self.cos: float = cos
        self.sin: float = sin
        self.length: int = length

    def __call__(self, cos: float, sin: float, length: int) -> tuple[np.ndarray]:
        """ """
        return np.full(length, cos), np.full(length, sin)
