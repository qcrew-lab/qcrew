import pprint
import random

from qcrew.control.modes.mode import Mode, ReadoutMode
from qcrew.control.instruments.quantum_machines.qm_config_builder import QMConfigBuilder

class TestLabBrick:
    def __init__(self, frequency):
        self.frequency = frequency

    def __repr__(self):
        return f"{self.frequency = }"

class TestMixerTuner:
    def tune(self, mode):
        mode.offsets = {
            "I": random.uniform(-0.1, 0.1),
            "Q": random.uniform(-0.1, 0.1),
            "G": random.uniform(-0.25, 0.25),
            "P": random.uniform(-0.25, 0.25),
        }

control_mode = Mode(
    name = "qubit",
    lo = TestLabBrick(frequency=5e9),
    int_freq = -50e6,
    ports = {"I": 1, "Q": 2}
)

readout_mode = ReadoutMode(
    name = "rr",
    lo = TestLabBrick(frequency=8e9),
    int_freq = -75e6,
    ports = {"I": 3, "Q": 4, "out": 1},
    time_of_flight = 180,
    smearing = 0,
)

tmt = TestMixerTuner()
tmt.tune(control_mode)

pprint.pp(control_mode.parameters)
pprint.pp(readout_mode.parameters)

qcb = QMConfigBuilder(control_mode)
pprint.pp(qcb.config)
