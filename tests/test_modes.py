""" Test round-trip loading and saving of dummy modes from/to yml config """

import pathlib
import pprint

import qcrew.helpers.yamlizer as yml
from test_labbrick import TestLabBrick
from qcrew.control.modes import Qubit, Readout
from qcrew.helpers import logger

CONFIGPATH = pathlib.Path.cwd() / "tests/test_modes.yml"

modes = yml.load(CONFIGPATH)
logger.success(f"Loaded {len(modes)} test modes from {CONFIGPATH}")
for mode in modes:
    logger.info(f"Printing {mode} parameters...")
    pprint.pp(mode.parameters)
    print()

logger.info(f"Saving test modes to {CONFIGPATH}")
yml.save(modes, CONFIGPATH)
