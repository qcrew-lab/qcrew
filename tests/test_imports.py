""" Test script to check if classes/modules from qcrew are imported successfully """

from qcrew.helpers import logger
from qcrew.control import Stagehand
from qcrew.control.instruments import LabBrick, Sa124
from qcrew.control.instruments.qm import QMConfigBuilder
from qcrew.control.instruments.meta import MixerTuner
from qcrew.control.modes import Cavity, Mode, Qubit, Readout
from qcrew.control.pulses import ConstantPulse, GaussianPulse
from qcrew.control.stage import stage_setup, stage_teardown

imports = {
    Stagehand,
    LabBrick,
    Sa124,
    QMConfigBuilder,
    MixerTuner,
    Cavity,
    Mode,
    Qubit,
    Readout,
    ConstantPulse,
    GaussianPulse,
    stage_setup,
    stage_teardown,
}

logger.info(f"Successfully imported {len(imports)} objects from qcrew!")
