""" """

from numbers import Real
from typing import ClassVar

import numpy as np

from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized
from qcrew.helpers.yamlizer import Yamlizable

BASE_PULSE_AMP = 0.2  # in V
CLOCK_CYCLE = 4  # in ns


class Pulse(Parametrized, Yamlizable):
    """ """

    _parameters: ClassVar[set[str]] = {"length", "ampx"}

    def __init__(
        self,
        *,  # enforce keyword-only arguments
        length: int = 400,
        ampx: float = 1.0,
        integration_weights=None,
    ) -> None:
        """ """
        self.length: int = length
        self.ampx: float = ampx

        self.is_readout_pulse: bool = False
        self.integration_weights = None
        if integration_weights is not None:
            self.integration_weights = integration_weights
            self.is_readout_pulse = True
            self._update_integration_weights("length")

        self.has_mix_waveforms: bool = True  # qcrew's default use case

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}[{self.type_}]{self.parameters}"

    def __call__(self, **parameters: Real) -> None:
        """ """
        for name, value in parameters.items():
            is_attribute = hasattr(self, name)
            if is_attribute and value is not None:
                setattr(self, name, value)
                if self.is_readout_pulse:
                    self._update_integration_weights(name)
            elif not is_attribute:
                cls_name = type(self).__name__
                logger.warning(f"Parameter '{name}' must be an attribute of {cls_name}")
        logger.success(f"Set {self}")

    def _update_integration_weights(self, key: str) -> None:
        """ """
        do_update = key == "length" and self.integration_weights.is_pinned
        if do_update:
            new_iw_len = int(self.length / CLOCK_CYCLE)
            self.integration_weights.length = new_iw_len
            logger.debug(f"Set integration weights len = {new_iw_len}")

    @property  # waveform amplitude samples getter
    def samples(self) -> tuple[np.ndarray]:
        """ """
        logger.error("Abstract method must be implemented by subclass(es)")
        raise NotImplementedError("Can't call `samples` on Pulse instance")

    @property  # pulse type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "measurement" if self.is_readout_pulse else "control"


class IQPulse(Pulse):
    """ """

    _parameters: ClassVar[set[str]] = Pulse._parameters | {
        "i_wave",
        "q_wave",
    }

    def __init__(self, i_wave, q_wave, ampx: float = 1.0, pad: int = 0) -> None:
        """ """
        self.i_wave, self.q_wave = "NA", "NA"  # to avoid yamlizing np arrays
        self.iwave, self.qwave = i_wave, q_wave  # underscore omitted on purpose

        self.pad = pad
        
        if len(i_wave) != len(q_wave):
            raise ValueError("i_wave and q_wave must be of same length")

        length = len(i_wave)
        if length % 4 != 0:
            self.pad = 4 - length % 4
            length += self.pad

        super().__init__(length=length, ampx=ampx, integration_weights=None)

    @property
    def samples(self):
        """ """
        i_wave = np.real(self.iwave)
        q_wave = np.imag(self.qwave)

        if self.pad != 0:
            pad_zeros = np.zeros(self.pad)
            i_wave = np.concatenate((i_wave, pad_zeros), axis=0)
            q_wave = np.concatenate((q_wave, pad_zeros), axis=0)

        return i_wave, q_wave
