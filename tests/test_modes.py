""" Test script for initializing Modes"""
import pprint
import pathlib
from qcrew.control.modes.qubit import Qubit
from qcrew.control.modes.readout_resonator import ReadoutResonator
import qcrew.helpers.yamlizer as yml
from tests.test_labbrick import TestLabBrick
from qcrew.control.modes.mode import Mode, ReadoutMode

CONFIGPATH = pathlib.Path.cwd() / "tests/test_config.yml"
modes = yml.load(CONFIGPATH)
qubit, rr = modes[0], modes[1]

"""qubit = Qubit(
    name = "QUBIT",
    lo = TestLabBrick(frequency=5e9),
    int_freq = -50e6,
    ports = {"I": 1, "Q": 2}
)

rr = ReadoutResonator(
    name = "RR",
    lo = TestLabBrick(frequency=8e9),
    int_freq = -75e6,
    ports = {"I": 3, "Q": 4, "out": 1},
)
"""
