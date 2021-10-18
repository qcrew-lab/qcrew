""" get ge state trajectory v5 """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np
from qcrew.helpers.state_discriminator.DCoffsetCalibrator import (
    DCoffsetCalibrator,
)


if __name__ == "__main__":

    with Stagehand() as stage:

        rr = stage.RR
        qubit = stage.QUBIT
        qmm = stage._qmm
        config = stage.QM.get_config()

        df_offset = DCoffsetCalibrator.calibrate(qmm, config, "RR")