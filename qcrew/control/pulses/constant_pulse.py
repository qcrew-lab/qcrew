""" """

import numpy as np
from typing import ClassVar
from qcrew.control.pulses import integration_weights
from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse


class ConstantPulse(Pulse):
    """ """

    def __call__(self, length: int, ampx: float = None) -> None:
        """ """
        super().__call__(length=length, ampx=ampx)

    @property
    def samples(self) -> tuple[np.ndarray]:
        i_wave = np.full(self.length, (BASE_PULSE_AMP * self.ampx))
        q_wave = np.zeros(self.length)
        return i_wave, q_wave


class PadConstantPulse(Pulse):
    """ """

    _parameters: ClassVar[set[str]] = Pulse._parameters | {
        "pad",
        "const_length",
    }

    def __init__(
        self,
        ampx: float = 1.0,
        pad: int = 1000,
        const_length: int = 1000,
        integration_weights=None,
    ) -> None:
        self.const_length = const_length
        self.pad = pad
        super().__init__(
            length=const_length + 2 * pad,
            ampx=ampx,
            integration_weights=integration_weights,
        )

    def __call__(self, length: int, ampx: float = None, pad: int = None) -> None:
        """ """
        super().__call__(
            length=length + 2 * pad, ampx=ampx, pad=pad, const_length=length
        )

    @property
    def samples(self) -> tuple[np.ndarray]:
        i_wave = np.full(self.const_length, (BASE_PULSE_AMP * self.ampx))
        if self.pad is not None:
            pad_zeros = np.zeros(self.pad)
            i_wave = np.concatenate((pad_zeros, i_wave, pad_zeros), axis=0)
        # q_wave = np.zeros(self.length)
        q_wave = np.zeros(len(i_wave))
        return i_wave, q_wave
