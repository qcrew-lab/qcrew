""" Test loading dummy instruments from yml config """

import pathlib

import qcrew.helpers.yamlizer as yml
from tests.test_labbrick import TestLabBrick
from tests.test_sa124 import TestSa124
from qcrew.helpers import logger

CONFIGPATH = pathlib.Path.cwd() / "tests/test_instruments.yml"

instruments = yml.load(CONFIGPATH)
logger.success(f"Loaded {len(instruments)} test instruments from {CONFIGPATH}")
