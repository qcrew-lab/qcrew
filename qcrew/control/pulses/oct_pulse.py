""" """

from pathlib import Path

import numpy as np

from qcrew.control.pulses.pulse import Pulse


class OptimalControlPulse(Pulse):
    """ """

    def __init__(self, path: Path, ampx: float = 1.0, pad: int = 0) -> None:
        """ """
        self.path = path
        self.pad = pad

        npzfile = np.load(Path(self.path))
        self.oct_pulse = npzfile["oct_pulse"]

        super().__init__(length=len(self.oct_pulse), ampx=ampx, integration_weights=None)

    @property
    def samples(self):
        """ """
        i_wave = np.real(self.oct_pulse)
        q_wave = np.imag(self.oct_pulse)
        return i_wave, q_wave
