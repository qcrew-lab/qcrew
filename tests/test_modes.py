""" Test script for initializing Modes"""
from pprint import pp
from qcrew.control.modes.mode import Mode, ReadoutMode

class TestLabBrick:
    def __init__(self, frequency):
        self.frequency = frequency

    @property
    def parameters(self):
        return {"frequency": self.frequency}

qubit = Mode(
    name = "qubit",
    lo = TestLabBrick(frequency=5e9),
    int_freq = -50e6,
    ports = {"I": 1, "Q": 2}
)

rr = ReadoutMode(
    name = "rr",
    lo = TestLabBrick(frequency=8e9),
    int_freq = -75e6,
    ports = {"I": 3, "Q": 4, "out": 1},
    time_of_flight = 180,
    smearing = 0,
)
