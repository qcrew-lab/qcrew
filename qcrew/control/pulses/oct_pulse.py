""" """

from pathlib import Path

import numpy as np

from qcrew.control.pulses.pulse import BASE_PULSE_AMP, Pulse

class OptimalControlPulse(Pulse):
      """ """
      
      def __init__(self, path: Path, ampx: float = .2, pad: int = 0) -> None:
    """ """
        self._path = path
        self.ampx = ampx
        self.pad = pad
            
        npzfile = np.load(Path(self._path))
        cavity_pulse = npzfile["cavity"]
        qubit_pulse = npzfile["qubit"]
        self.length = len(cavity_pulse)  # both pulses should have same length

    def __call__(
        self, *, sigma: float, chop: int = None, ampx: float = None, drag: float = None
    ) -> None:
        """ """
        length = int(sigma * chop) if chop is not None else int(sigma * self.chop)
        super().__call__(sigma=sigma, chop=chop, ampx=ampx, drag=drag, length=length)

