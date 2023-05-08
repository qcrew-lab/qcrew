""" """
from typing import ClassVar
import numpy as np
from qcrew.control.pulses.pulse import Pulse


class DigitalMarkerPulse(Pulse):
    """ """

    DEFAULT_SAMPLES: list[tuple[int, int]] = [(1, 0)]

    _parameters: ClassVar[set[str]] = Pulse._parameters | {
        "name",
        "sample_path",
    }

    def __init__(
        self,
        name: str,
        length: int = 400,
        ampx: float = 1.0,
        sample_path: str = None,
    ) -> None:
        """ """
        # Overwrites the value in Pulse parent class.
        self.has_mix_waveforms = False
        # [(value, length)] where value = 0 (LOW) or 1 (HIGH) and length is in ns
        # length = 0 means value will be played for remaining duration of the waveform
        self.name = name
        self.sample_path = sample_path
        # super().__init__(name=name, **parameters)
        super().__init__(length=length, ampx=ampx)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def samples(self) -> tuple[np.ndarray]:
        if self.sample_path == "default":
            return DigitalMarkerPulse.DEFAULT_SAMPLES
        else:
            return DigitalMarkerPulse.DEFAULT_SAMPLES

    # @property
    # def sample_path(self):
    #     return self._sample_path

    # @sample_path.setter
    # def sample_path(self, sample_path):
    #     self._sample_path = sample_path
