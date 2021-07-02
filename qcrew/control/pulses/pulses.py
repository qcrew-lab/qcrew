""" """

from numbers import Real
from typing import Any, ClassVar

import numpy as np
from qcrew.helpers.parametrizer import Parametrized
from qcrew.control.instruments.quantum_machines import BASE_AMP


class Pulse(Parametrized):

    _parameters: ClassVar[set[str]] = {"length"}

    def __init__(
        self,
        length: int,
        has_mix_waveforms: bool = True,
        integration_weights: dict[str, np.ndarray] = None,
    ) -> None:
        """ """
        self.length: int = length
        self.has_mix_waveforms: bool = has_mix_waveforms
        self.is_readout_pulse: bool = False
        if integration_weights is not None:
            self.is_readout_pulse = True
            self._parameters.add("integration_weights")
            self.integration_weights: dict[str, np.ndarray] = integration_weights

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}{self.parameters}"

    def __call__(self, **parameters: Real) -> None:
        """ """
        for name, value in parameters.items():
            if hasattr(self, name):
                setattr(self, name, value)

    @property  # waveform amplitude samples getter
    def samples(self) -> tuple[np.ndarray]:
        """ """
        raise NotImplementedError  # subclasses must implements

    @property  # pulse type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "measurement" if self.is_readout_pulse else "control"


class ConstantPulse(Pulse):
    """ """

    _parameters: ClassVar[set[str]] = Pulse._parameters | {"ampx"}

    def __init__(
        self,
        ampx: float = 1.0,
        length: int = 400,
        integration_weights: dict[str, np.ndarray] = None,
    ) -> None:
        """ """
        self.ampx: float = ampx
        super().__init__(length=length, integration_weights=integration_weights)

    @property
    def samples(self) -> tuple[np.ndarray]:
        i_wave = np.full(self.length, (BASE_AMP * self.ampx))
        q_wave = np.zeros(self.length)
        return i_wave, q_wave


class GaussianPulse(Pulse):
    _parameters: ClassVar[set[str]] = Pulse._parameters | {
        "sigma",
        "chop",
        "ampx",
        "drag",
    }

    def __init__(
        self,
        sigma: float,
        chop: int = 6,
        ampx: float = 1.0,
        drag: float = 0.0,
        integration_weights: dict[str, np.ndarray] = None,
    ) -> None:
        """ """
        self.sigma: float = sigma
        self.chop: int = chop
        self.ampx: float = ampx
        self.drag: float = drag
        length = int(sigma * chop)
        super().__init__(length=length, integration_weights=integration_weights)

    def __call__(self, sigma: float, chop: int, ampx: float, drag: float) -> None:
        """ """
        super().__call__(sigma=sigma, chop=chop, ampx=ampx, drag=drag)
        self.length = int(sigma * chop)

    @property
    def samples(self) -> tuple[np.ndarray]:
        start, stop = -self.chop / 2 * self.sigma, self.chop / 2 * self.sigma
        ts = np.linspace(start, stop, self.length)
        i_wave = BASE_AMP * self.ampx * np.exp(-(ts ** 2) / (2.0 * self.sigma ** 2))
        q_wave = self.drag * (np.exp(0.5) / self.sigma) * i_wave
        return i_wave, q_wave
