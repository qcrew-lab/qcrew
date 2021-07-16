""" """

from typing import ClassVar

import numpy as np

from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse


class GaussianPulse(Pulse):
    """ """

    _parameters: ClassVar[set[str]] = Pulse._parameters | {
        "sigma",
        "chop",
        "drag",
    }

    def __init__(
        self,
        sigma: float,
        chop: int = 6,
        ampx: float = 1.0,
        drag: float = 0.0,
    ) -> None:
        """ """
        self.sigma: float = sigma
        self.chop: int = chop
        self.drag: float = drag
        length = int(sigma * chop)
        super().__init__(length=length, ampx=ampx, integration_weights=None)

    def __call__(
        self, *, sigma: float, chop: int = None, ampx: float = None, drag: float = None
    ) -> None:
        """ """
        length = int(sigma * chop) if chop is not None else int(sigma * self.chop)
        super().__call__(sigma=sigma, chop=chop, ampx=ampx, drag=drag, _length=length)

    @property
    def samples(self) -> tuple[np.ndarray]:
        """ """
        start, stop = -self.chop / 2 * self.sigma, self.chop / 2 * self.sigma
        ts = np.linspace(start, stop, self._length)
        exponential = np.exp(-(ts ** 2) / (2.0 * self.sigma ** 2))
        i_wave = BASE_PULSE_AMP * self.ampx * exponential
        q_wave = self.drag * (np.exp(0.5) / self.sigma) * i_wave
        return i_wave, q_wave
