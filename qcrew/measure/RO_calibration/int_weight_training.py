""" Readout integration weights training for single-shot readout """

from qcrew.control.instruments.meta.readout_trainer import ReadoutTrainer
from qcrew.control import Stagehand

from pathlib import Path
import numpy as np
import datetime

if __name__ == "__main__":
    with Stagehand() as stage:
        rr, qubit = stage.RR, stage.QUBIT
        qm = stage.QM

        # Save file with today's date
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_opt_weights.npz")
        file_path = Path("C:/Users/qcrew/Desktop/qcrew/qcrew/config/weights") / date_str

        params = {
            "reps": 20_000,
            "wait_time": 600_000,  # ns
            "qubit_pi_pulse": "qubit_gaussian_96ns_pi_pulse",  # pulse to excite qubit
            "weights_file_path": file_path,
        }

        # ddrop_params = {
        #     "rr_ddrop_freq": int(-50.4e6),
        #     "rr_ddrop": "ddrop_pulse",
        #     "qubit_ddrop": "ddrop_pulse",
        #     "qubit_ef_mode": stage.QUBIT_EF,
        #     "steady_state_wait": 2000,
        # }
        # ro_trainer = ReadoutTrainer(rr, qubit, qm, ddrop_params=ddrop_params, **params)
        ro_trainer = ReadoutTrainer(rr, qubit, qm, **params)
        ro_trainer.train_weights()

        ## Make sure to run this script every time the readout pulse is changed!!
