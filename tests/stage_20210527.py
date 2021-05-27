""" Temporary stage file for the QMConfigBuilder demo """

import random
from qcrew.instruments.meta import Qubit, ReadoutResonator

# make fake instruments as I currently don't have access to the physical instruments
class FakeLabBrick:
    """Stand in for an actual LabBrick"""

    def __init__(self, frequency):
        self._frequency = frequency

    @property
    def frequency(self) -> float:
        return self._frequency

    @frequency.setter
    def frequency(self, frequency) -> None:
        self._frequency = frequency


class FakeMixerTuner:
    """Stand in for an actual MixerTuner"""

    def tune(self, *elements):
        for element in elements:
            offsets = {
                "I": random.uniform(-0.5, 0.5),
                "Q": random.uniform(-0.5, 0.5),
                "G": random.uniform(-0.36, 0.36),
                "P": random.uniform(-0.36, 0.36),
            }
            element.mixer.offsets = offsets


# START OF STAGE FILE
qubit_parameters = {
    "name": "qubit",
    "lo": FakeLabBrick(frequency=5e9),
    "int_freq": -50e6,
    "ports": {"I": 1, "Q": 2},
}
qubit = Qubit(**qubit_parameters)

rr_parameters = {
    "name": "rr",
    "lo": FakeLabBrick(frequency=7e9),
    "int_freq": -60e6,
    "ports": {"I": 3, "Q": 4, "out": 1},
}
rr = ReadoutResonator(**rr_parameters)
# END OF STAGE FILE
