""" """

import numpy as np

from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse


class ConstantPulse(Pulse):
    """ """

    def __call__(self, length: int, ampx: float = None) -> None:
        """ """
        super().__call__(_length=length, ampx=ampx)

    @property
    def samples(self) -> tuple[np.ndarray]:
        i_wave = np.full(self._length, (BASE_PULSE_AMP * self.ampx))
        q_wave = np.zeros(self._length)
        return i_wave, q_wave
