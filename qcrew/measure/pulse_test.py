""" get ge state trajectory v5 """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np


if __name__ == "__main__":

    with Stagehand() as stage:
        rr = stage.RR
        qubit = stage.QUBIT
        # rr.opt_readout_pulse(threshold=0.1, pad=1000, length=1000)
        # rr.readout_pulse(pad=0, length=1000)


