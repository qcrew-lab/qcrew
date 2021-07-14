""" """

import numpy as np

from qcrew.control.instruments.quantum_machines import BASE_AMP
from qcrew.control.pulses.pulse import Pulse


class ConstantPulse(Pulse):
    """ """

    def __call__(self, length: int, ampx: float = None) -> None:
        """ """
        super().__call__(_length=length, ampx=ampx)

    @property
    def samples(self) -> tuple[np.ndarray]:
        return np.full(self._length, (BASE_AMP * self.ampx)), np.zeros(self._length)
