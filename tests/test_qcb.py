import pprint
import pathlib

from qcrew.control.modes.mode import Mode, ReadoutMode
from qcrew.control.instruments.quantum_machines.qm_config_builder import QMConfigBuilder
from qcrew.control.pulses.pulses import Pulse, ConstantPulse, GaussianPulse
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
qubit.lo_freq = 5.0e9
rr.lo_freq = 8.0e9
config = qcb.config

# change int freq
qubit.int_freq = -50e6
config = qcb.config

# change ports
qubit.ports = {"I": 1, "Q": 2}

# change offsets
#tmt = TestMixerTuner()
#tmt.tune(qubit, rr)
#config = qcb.config

# change operations
rr.readout_pulse(length=28)
rr.gaussian_pulse(sigma=6)
qubit.constant_pulse(length=20, ampx=1.0)
qubit.gaussian_pulse(sigma=4, chop=4, ampx=1.5)
config = qcb.config

# save modes to config
yml.save(modes, CONFIGPATH)
