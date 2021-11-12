""" get ge state trajectory v5 """

from qcrew.control import Stagehand
from qcrew.measure.state_discriminator.helpers.dc_offset_calibrator import (
    DCoffsetCalibrator,
)

if __name__ == "__main__":

    with Stagehand() as stage:

        rr = stage.RR
        qubit = stage.QUBIT
        qmm = stage._qmm
        config = stage.QM.get_config()

        df_offset = DCoffsetCalibrator.calibrate(qmm, config, rr.name)
