import pprint
import pathlib

from qcrew.control.modes.mode import Mode, ReadoutMode
from qcrew.control.instruments.quantum_machines.qm_config_builder import QMConfigBuilder
from qcrew.control.pulses.pulses import ConstantPulse
from tests.test_labbrick import TestLabBrick
from tests.test_mixer_tuner import TestMixerTuner
import qcrew.helpers.yamlizer as yml
from qcrew.control.modes.qubit import Qubit
from qcrew.control.modes.readout_resonator import ReadoutResonator

# get modes from yml config
CONFIGPATH = pathlib.Path.cwd() / "tests/test_config.yml"
modes = yml.load(CONFIGPATH)
qubit, rr = modes[0], modes[1]
qcb = QMConfigBuilder(qubit, rr)
config = qcb.config

# change lo freq
qubit.lo_freq = 5.5e9
rr.lo_freq = 8.5e9
config = qcb.config

# change int freq
qubit.int_freq = -55e6
config = qcb.config

# change ports
qubit.ports = {"I": 3, "Q": 4}
config = qcb.config

# change offsets
tmt = TestMixerTuner()
tmt.tune(qubit, rr)
config = qcb.config

# change operations
rr.readout_pulse.length = 24
qubit.constant_pulse(0.5, 500)
config = qcb.config
qubit.gaussian_pulse(0.5, 20, 3)
config = qcb.config

qubit.operations = {
    "saturation_pulse": ConstantPulse(0.5, 1200)
}
config = qcb.config

rr.readout_pulse(0.25, 100)
