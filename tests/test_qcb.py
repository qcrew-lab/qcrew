import pprint
import random

from qcrew.control.modes.mode import Mode, ReadoutMode
from qcrew.control.instruments.quantum_machines.qm_config_builder import QMConfigBuilder
from qcrew.control.pulses.pulses import ConstantPulse

class TestLabBrick:
    def __init__(self, frequency):
        self.frequency = frequency

    @property
    def parameters(self):
        return {"frequency": self.frequency}

class TestMixerTuner:
    def tune(self, mode):
        mode.offsets = {
            "I": random.uniform(-0.1, 0.1),
            "Q": random.uniform(-0.1, 0.1),
            "G": random.uniform(-0.25, 0.25),
            "P": random.uniform(-0.25, 0.25),
        }

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


tmt = TestMixerTuner()
tmt.tune(qubit)

pprint.pp(qubit.parameters)
pprint.pp(rr.parameters)

qcb = QMConfigBuilder(qubit, rr)
config = qcb.config


qubit.lo_freq = 5.5e9
config = qcb.config
qubit.int_freq = -55e6
config = qcb.config
qubit.ports = {"I": 3, "Q": 4}
config = qcb.config
tmt.tune(qubit)
config = qcb.config


qubit.constant_pulse(0.5, 500)
config = qcb.config
qubit.gaussian_pulse(0.5, 20, 3)
config = qcb.config

qubit.operations = {
    "saturation_pulse": ConstantPulse(0.5, 1200)
}
config = qcb.config

rr.readout_pulse(0.25, 100)
