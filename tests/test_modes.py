""" Test loading dummy modes from yml config """

import pathlib
import pprint

import qcrew.helpers.yamlizer as yml
from tests.test_labbrick import TestLabBrick
from qcrew.control.modes import Qubit, Readout
from qcrew.helpers import logger

CONFIGPATH = pathlib.Path.cwd() / "tests/test_modes.yml"

modes = yml.load(CONFIGPATH)
logger.success(f"Loaded {len(modes)} test modes from {CONFIGPATH}")
logger.info("Printing mode parameters...")
for mode in modes:
    pprint.pp(mode.parameters)
    print()
