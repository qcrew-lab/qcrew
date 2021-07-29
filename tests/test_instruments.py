""" Test round-trip loading and saving of dummy instruments from/to yml config """

import pathlib
import pprint

import qcrew.helpers.yamlizer as yml
from tests.test_labbrick import TestLabBrick
from tests.test_sa124 import TestSa124
from qcrew.helpers import logger

CONFIGPATH = pathlib.Path.cwd() / "tests/test_instruments.yml"

instruments = yml.load(CONFIGPATH)

try:
    num_instruments = len(instruments)
except TypeError:
    logger.error(f"No objects found in {CONFIGPATH.name}, please check the config file")
else:
    logger.success(f"Loaded {num_instruments} test instruments from {CONFIGPATH}")
    for instrument in instruments:
        logger.info(f"Printing {instrument} parameters...")
        pprint.pp(instrument.parameters)
        print()

    logger.info(f"Saving test instruments to {CONFIGPATH}")
    yml.save(instruments, CONFIGPATH)
