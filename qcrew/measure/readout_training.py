""" Readout integration weights training for single-shot readout """

from qcrew.control.instruments.meta.readout_trainer import ReadoutTrainer
from qcrew.control import Stagehand

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    with Stagehand() as stage:
        rr, qubit = stage.RR, stage.QUBIT

        params = {
            "reps": 1000,
            "wait_time": 100000,  # ns
            "readout_pulse": "readout_pulse",  # pulse to be trained
            "qubit_pi_pulse": "pi",  # pulse to excite qubit
            "weights_file_path": Path("C:/Users/qcrew/Desktop/qcrew/qcrew/config")
            / "opt_readout_weights_F.npz",
        }

        # get an already configured qm after making changes to modes
        qm = stage.QM
        ro_trainer = ReadoutTrainer(rr, qubit, qm, params)
        env_g, env_e, weights, squeezed_weights = ro_trainer.train()
        plt.plot(np.real(env_g))
        plt.plot(np.imag(env_g))
        plt.show()

        plt.plot(np.real(env_e))
        plt.plot(np.imag(env_e))
        plt.show()

        print(weights.shape)
        print(squeezed_weights.shape)
