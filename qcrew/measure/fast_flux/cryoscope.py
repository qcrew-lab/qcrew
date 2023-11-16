"""
A python class describing a readout resonator spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from signal import signal
from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.control.pulses import constant_pulse
from qcrew.measure.experiment import Experiment
from qm import qua

import numpy as np
import h5py
from datetime import datetime

# ---------------------------------- Class -------------------------------------


class Cryoscope(Experiment):

    name = "cryoscope"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, pulse_len_sweep, fit_fn=None, **other_params):

        self.fit_fn = fit_fn
        self.qubit_op = qubit_op
        self.operation_sweep = [(x, y) for y in [0.25, 0.0] for x in pulse_len_sweep]
        self.internal_sweep = [elem[0] for elem in self.operation_sweep]
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr, qubit, flux) = self.modes  # get the modes

        ### To measure <X>, both pi2 pulses must be phase = 0.25.
        ### To measure <Y>, the second pi2 pulse is phase = 0
        for flux_len, second_pi_phase in self.operation_sweep:
            qua.align()
            qubit.play(self.qubit_op, phase=0.25)
            qua.wait(int(600 // 4), qubit.name)
            flux.play(f"square_{flux_len}ns_filter_L2", ampx=-0.2)
            qubit.play(self.qubit_op, phase=second_pi_phase)
            qua.align(qubit.name, rr.name)
            qua.wait(300, rr.name)
            rr.measure((self.I, self.Q))  # measure qubit state
            if self.single_shot:  # assign state to G or E
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )
            qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

            self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    plot_parameters = {
        "xlabel": "Flux pulse length (cc)",
    }

    # Initialize an empty array to store values
    signal_list = np.array([])
    flux_len_list = np.array([])

    path = "C:\\Users\\qcrew\\Desktop\\qcrew\\qcrew\\config\\cryoscope\\"
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S_")

    cryoscope_filename = path + current_datetime + f"cryoscope.npz"
    for i in range(5):

        flux_len_slice = list(np.arange(100 * i, 100 * (i + 1), 1))
        parameters = {
            "modes": ["RR", "QUBIT", "FLUX"],
            "reps": 50000,
            "wait_time": 40e3,  # 1e6,
            "pulse_len_sweep": flux_len_slice,
            "plot_quad": "I_AVG",
            "qubit_op": "gaussian_pi2",
            "fetch_period": 3,
        }
        data_tag = "state" if parameters.get("single_shot") else parameters["plot_quad"]

        experiment = Cryoscope(**parameters)
        experiment.setup_plot(**plot_parameters)
        prof.run(experiment)

        with h5py.File(experiment._filename, "r") as file:
            data = file["data"]
            sig = np.array(data[data_tag])
            freqs = np.array(data["internal sweep"])

            signal_list = np.concatenate((signal_list, sig))
            flux_len_list = np.concatenate((flux_len_list, flux_len_slice))
            np.savez(cryoscope_filename, signal=signal_list, flux_len=flux_len_list)
