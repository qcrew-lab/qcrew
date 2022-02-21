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
        qubit, qubit_name = stage.modes[0], stage.modes[0].name
        rr, rr_name = stage.modes[1], stage.modes[1].name

        timediff = TimeDiffCalibrator(qmm, old_config, rr_name, reps=1)
        timediff.calibrate(simulate=False)
