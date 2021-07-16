""" Test stage and stagehand with actual instruments """

import pprint
import pathlib
import matplotlib.pyplot as plt
import qcrew.helpers.yamlizer as yml
from qcrew.control.instruments.vaunix.labbrick import LabBrick
from qcrew.control.instruments.signal_hound.sa124 import Sa124

CONFIGPATH = pathlib.Path.cwd() / "configs/coax_a/instruments.yml"
instruments = yml.load(CONFIGPATH)
lb_qubit, lb_rr, sa = (*instruments,)
