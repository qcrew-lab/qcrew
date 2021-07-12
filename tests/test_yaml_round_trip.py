""" Test yaml round trip with spectrum and analysis and mixer tuning """

import pprint
import pathlib
from qcrew.control.modes.qubit import Qubit
from qcrew.control.modes.readout_resonator import ReadoutResonator
from qcrew.control.pulses.pulses import Pulse, ConstantPulse, GaussianPulse
from qcrew.control.instruments.vaunix.labbrick import LabBrick
from qcrew.control.instruments.signal_hound.sa124 import Sa124
import qcrew.helpers.yamlizer as yml
from qcrew.control.instruments.quantum_machines.qm_config_builder import QMConfigBuilder
from qm.QuantumMachinesManager import QuantumMachinesManager
from qcrew.control.instruments.mixer_tuner import MixerTuner
from qm.qua import program, infinite_loop_
import matplotlib.pyplot as plt

CONFIGPATH = pathlib.Path.cwd() / "tests/test_stage.yml"
objects_ = yml.load(CONFIGPATH)
qubit, rr, sa = objects_[0], objects_[1], objects_[2]
modes = (qubit, rr)

qcb = QMConfigBuilder(*modes)
qm_config = qcb.config

qmm = QuantumMachinesManager()
qm = qmm.open_qm(qm_config)

mxrtnr = MixerTuner(sa, qm, *modes)
mxrtnr.tune()

with program() as qua_test:
    with infinite_loop_():
        qubit.play("constant_pulse")

job = qm.execute(qua_test)

yml.save(objects_, CONFIGPATH)
