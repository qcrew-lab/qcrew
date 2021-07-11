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
rr.readout_pulse(length=24)
rr.gaussian_pulse(sigma=4)
qubit.constant_pulse(length=16, ampx=1.0)
qubit.gaussian_pulse(sigma=4, chop=4, ampx=1.2)
config = qcb.config

qubit.operations = {
    "saturation_pulse": ConstantPulse(length=28)
}
config = qcb.config

qubit.remove_operation("saturation_pulse")
config = qcb.config

# save modes to config
yml.save(modes, CONFIGPATH)
