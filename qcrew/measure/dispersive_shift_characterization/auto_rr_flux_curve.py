"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import Stagehand
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qcrew.analyze import fit
from qm import qua
import matplotlib.pyplot as plt
import numpy as np
import h5py
from datetime import datetime

# ---------------------------------- Class -------------------------------------


class RRSpectroscopy(Experiment):

    name = "rr_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, fit_fn=None, **other_params):

        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr,) = self.modes  # get the modesz
        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequenc
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -56e6
    x_stop = -42e6
    x_step = 0.05e6

    current_start = -26.0e-3
    current_stop = 26.0e-3
    current_step = 2e-3
    current_sweep = np.arange(current_start, current_stop, current_step)

    parameters = {
        "modes": ["RR"],
        "reps": 1000,
        "wait_time": 20000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "fit_fn": "gaussian",
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {"skip_plot": False, "plot_err": False}
    data_tag = "state" if parameters.get("single_shot") else parameters["plot_quad"]

    # Initialize an empty array to store values
    rr_freq_list = np.array([])
    current_list = np.array([])

    path = "C:\\Users\\qcrew\\Desktop\\qcrew\\qcrew\\config\\rrfreq_vs_current\\"
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S_")
    rr_freq_filename = path + current_datetime + "rr_current.npz"

    for current in current_sweep:

        with Stagehand() as stage:
            yoko = stage.YOKO
            rr = stage.RR
            yoko.ramp(current, yoko.level, np.abs(0.01e-3))
            rr_LO = rr.lo_freq

        experiment = RRSpectroscopy(**parameters)
        experiment.setup_plot(**plot_parameters)
        prof.run(experiment)

        with h5py.File(experiment._filename, "r") as file:
            data = file["data"]
            state = np.array(data[data_tag])
            freqs = np.array(data["x"])
            params = fit.do_fit("gaussian", freqs, state)
            rr_freq = rr_LO + float(params["x0"].value)

            print(rr_freq)
            rr_freq_list = np.append(rr_freq_list, rr_freq)
            current_list = np.append(current_list, current)
            np.savez(rr_freq_filename, rr_freq=rr_freq_list, currents=current_list)
