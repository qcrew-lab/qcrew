""" Readout integration weights training for single-shot readout """

from qcrew.control.instruments.meta.readout_trainer import ReadoutTrainer
from qcrew.control import Stagehand

if __name__ == "__main__":
    with Stagehand() as stage:
        rr, qubit = stage.RR, stage.QUBIT
        qm = stage.QM

        params = {
            "reps": 10000,
            "wait_time": 600000,  # ns
            "qubit_pi_pulse": "pi",  # pulse to excite qubit
        }

        ro_trainer = ReadoutTrainer(rr, qubit, qm, params)
        ro_trainer.calculate_threshold()

        ## Make sure to run this script every time the readout pulse is changed!!
