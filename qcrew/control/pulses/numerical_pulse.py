""" """

from pathlib import Path

import numpy as np

from qcrew.control.pulses.pulse import Pulse


class NumericalPulse(Pulse):
    """ """

    def __init__(self, path: Path, ampx: float = 1.0, pad: int = 0) -> None:
        """ """
        self.path = path
        self.pad = pad

        npzfile = np.load(Path(self.path))
        self.oct_pulse = npzfile["oct_pulse"]
        length = len(self.oct_pulse)
        if length % 4 != 0:
            self.pad = 4 - length % 4
            length += self.pad

        super().__init__(length=length, ampx=ampx, integration_weights=None)

    @property
    def samples(self):
        """ """
        i_wave = np.real(self.oct_pulse) * self.ampx
        q_wave = np.imag(self.oct_pulse) * self.ampx

        if self.pad != 0:
            pad_zeros = np.zeros(self.pad)
            i_wave = np.concatenate((i_wave, pad_zeros), axis=0)
            q_wave = np.concatenate((q_wave, pad_zeros), axis=0)

        return i_wave, q_wave
