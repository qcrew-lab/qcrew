""" g e state discriminator """

from qm.QuantumMachinesManager import QuantumMachinesManager
from qcrew.control import Stagehand

from qcrew.control.instruments.meta.time_difference_calibrator import (
    TimeDiffCalibrator,
)


if __name__ == "__main__":

    with Stagehand() as stage:

        qmm = QuantumMachinesManager()
        old_config = stage.QM.get_config()
        #qubit, qubit_name = stage.QUBIT, stage.QUBIT.name
        rr, rr_name = stage.RR, stage.RR.name

        timediff = TimeDiffCalibrator(qmm, old_config, rr_name, reps=1)
        timediff.calibrate(simulate=False)
