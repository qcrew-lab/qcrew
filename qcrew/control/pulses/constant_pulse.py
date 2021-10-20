""" """

from time import thread_time
import numpy as np
from typing import ClassVar
from qcrew.control.pulses import integration_weights
from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse


class ConstantPulse(Pulse):
    """ """

    _parameters: ClassVar[set[str]] = Pulse._parameters | {
        "pad",
        "threshold",
        "const_length",
    }

    def __init__(
        self,
        length: int,
        ampx: float = 1.0,
        pad: int = None,
        threshold: float = None,
        integration_weights=None,
    ) -> None:
        """ """
        self.pad = pad
        self.threshold = threshold

        # if length and (not const_length):
        #     self.pad = pad or 0
        #     if length > self.pad:
        #         self.const_length = length - self.pad
        #     else:
        #         raise ValueError("length should be larger than pad")
        # elif (not length) and const_length:
        #     self.pad = pad or 0
        #     self.const_length = const_length
        #     length = self.const_length + self.pad

        super().__init__(
            length=length, ampx=ampx, integration_weights=integration_weights
        )

    def __call__(
        self,
        const_length: int = None,
        ampx: float = None,
        pad: int = None,
        threshold: float = None,
        length: int = None,
    ) -> None:
        """ """
        if const_length and (not pad) and (not length):
            length = const_length + self.pad
        elif const_length and pad and (not length):
            length = const_length + pad
        elif (not const_length) and pad and (not length):
            length = self.const_length + pad
        elif (not const_length) and (not pad) and length:
            if length > self.const_length:
                pad = length - self.const_length
            else:
                const_length = length
                pad = 0
        elif (not const_length) and pad and length:
            if length > pad:
                const_length = length - pad
            else:
                raise ValueError("length should be larger than pad")

        super().__call__(
            const_length=const_length,
            length=length,
            ampx=ampx,
            pad=pad,
            threshold=threshold,
        )

    @property
    def samples(self) -> tuple[np.ndarray]:
        i_wave = np.full(self.const_length, (BASE_PULSE_AMP * self.ampx))
        q_wave = np.zeros(self.length)

        if self.pad != 0:
            pad_zeros = np.zeros(self.pad)
            i_wave = np.concatenate((i_wave, pad_zeros), axis=0)

        return i_wave, q_wave
