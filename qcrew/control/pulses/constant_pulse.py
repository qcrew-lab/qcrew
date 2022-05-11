""" """

from time import thread_time
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


class ReadoutPulse(Pulse):
    """ """

    _parameters: ClassVar[set[str]] = Pulse._parameters | {
        "pad",
        "const_length",
        "threshold",
        "iw_path",
        "length",
    }

    def __init__(
        self,
        *,
        length: int = 400,
        ampx: float = 1.0,
        pad: int = 0,
        const_length: int = 400,
        threshold: float = None,
        integration_weights=None,
    ) -> None:
        if (pad is None) and (length is not None) and (const_length is not None):
            self.pad = length - const_length
        else:
            self.pad = pad
        if (const_length is None) and (pad is not None) and (length is not None):
            self.const_length = length - pad
        else:
            self.const_length = const_length

        if (length is None) and (pad is not None) and (const_length is not None):
            length = pad + const_length

        self.threshold = threshold
        # Saves the integration weights path as parameter if applicable
        try:
            self.iw_path = integration_weights.path
        except AttributeError:
            self.iw_path = None

        super().__init__(
            length=length, ampx=ampx, integration_weights=integration_weights
        )

    def __call__(
        self,
        *,
        length: int = None,
        pad: int = None,
        const_length: int = None,
        ampx: float = None,
        threshold: float = None,
    ) -> None:
        """ """

        if (length is not None) and (pad is None) and (const_length is None):
            pad = length - self.const_length
        elif (length is not None) and (pad is not None) and (const_length is None):
            const_length = length - pad
        elif (length is None) and (pad is not None) and (const_length is None):
            length = self.const_length + pad
        elif (length is None) and (pad is not None) and (const_length is not None):
            length = pad + const_length

        super().__call__(
            length=length,
            pad=pad,
            const_length=const_length,
            ampx=ampx,
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
