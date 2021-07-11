""" """

from numbers import Real
from typing import ClassVar

import numpy as np
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized
from qcrew.control.instruments.quantum_machines import BASE_AMP, CLOCK_CYCLE


class Pulse(Parametrized):
    """ """

    _parameters: ClassVar[set[str]] = {"length"}

    def __init__(
        self,
        length: int,
        has_mix_waveforms: bool = True,
        integration_weights = None,
    ) -> None:
        """ """
        self._length: int = length
        self.has_mix_waveforms: bool = has_mix_waveforms
        self.is_readout_pulse: bool = False
        self.integration_weights = integration_weights

        if self.integration_weights is not None:
            self._integration_weights_samples = self.integration_weights_samples
            self.is_readout_pulse = True

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}{self.parameters}[{self.type_}]"

    def __call__(self, **parameters: Real) -> None:
        """ """
        for name, value in parameters.items():
            is_attribute = hasattr(self, name)
            if is_attribute and value is not None:
                setattr(self, name, value)
            elif not is_attribute:
                cls_name = type(self).__name__
                logger.warning(f"Parameter '{name}' must be an attribute of {cls_name}")
        logger.success(f"Set {self}")

    @property  # pulse length getter
    def length(self) -> int:
        """ """
        return self._length

    @property  # waveform amplitude samples getter
    def samples(self) -> tuple[np.ndarray]:
        """ """
        logger.error("Abstract method must be implemented by subclass(es)")
        raise NotImplementedError("Can't call `samples` on Pulse instance")

    # NOTE TODO this is hard coded to return constant integration weights !!!
    @property  # integration weights samples getter
    def integration_weights_samples(self) -> dict[str, dict[str, np.ndarray]]:
        """ """
        if self.integration_weights is not None:
            iw_length = int(self._length / CLOCK_CYCLE)
            if not iw_length == self.integration_weights.length:
                logger.info("Updating ReadoutPulse integration weights...")
                self.integration_weights(ampx=1 / BASE_AMP, length=iw_length)
                samples = self.integration_weights.samples
                return {
                    "iwI": {
                        "cosine": samples[0],
                        "sine": samples[1],
                    },
                    "iwQ": {
                        "cosine": samples[1],
                        "sine": samples[0],
                    },
                }
            else:
                return self._integration_weights_samples
        else:
            logger.warning(f"No integration weights defined for {self}")

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
        length: int = 1000,
        integration_weights = None,
    ) -> None:
        """ """
        self.ampx: float = ampx
        super().__init__(length=length, integration_weights=integration_weights)

    def __call__(self, length: int, ampx: float = None) -> None:
        """ """
        super().__call__(_length=length, ampx=ampx)

    @property
    def samples(self) -> tuple[np.ndarray]:
        return np.full(self._length, (BASE_AMP * self.ampx)), np.zeros(self._length)


class GaussianPulse(Pulse):
    """ """

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
    ) -> None:
        """ """
        self.sigma: float = sigma
        self.chop: int = chop
        self.ampx: float = ampx
        self.drag: float = drag
        length = int(sigma * chop)
        super().__init__(length=length, integration_weights=None)

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
        i_wave = BASE_AMP * self.ampx * np.exp(-(ts ** 2) / (2.0 * self.sigma ** 2))
        q_wave = self.drag * (np.exp(0.5) / self.sigma) * i_wave
        return i_wave, q_wave
