"""
Stagehand returns a stage of instruments based on a config.
"""
from pathlib import Path
from types import SimpleNamespace

from qcrew.helpers import logger
from qcrew.instruments import Instrument

# set up the stage
# config is a yaml file where each document consist of a single node
# the node specifies an initial state for an instrument
# the instrument is identified from its yaml tag
# the initial state is defined by a mapping
# in the mapping, keys are instrument parameter names
# and values are initial parameter values
# should throw an error if node in document is not an instrument node
# must return a stage object
def setup():
    pass


# catch error if path errors
# catch error if yaml errors

# only Instrument type objects can be added to Stage
class Stage(SimpleNamespace):
    """
    TODO write docu
    """
    