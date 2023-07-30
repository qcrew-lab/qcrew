"""
A python class describing a vacuum rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

import numpy as np

# ---------------------------------- Class -------------------------------------
# delete this comment


class VacuumRabi(Experiment):

    name = "vacuum_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="", **other_params):
        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        # self.flux_pulse = flux_pulse
        self.internal_sweep = [20, 36, 44]
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        for flux_len in self.internal_sweep:
            qubit.play(self.qubit_op)  # play pi qubit pulse
            qua.align(qubit.name, flux.name)
            flux.play(f"20230724_square_{flux_len}ns", ampx=self.x) #ns
            qua.wait(int((400 + 24) // 4), rr.name, qubit.name)  # cc
            rr.measure((self.I, self.Q))  # measure qubit state
            if self.single_shot:  # assign state to G or E7
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )
            qua.wait(int(self.wait_time // 4))  # wait system reset
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    # x_start = 295
    # x_stop = 605
    # x_step = 4

    x_start = -0.3
    x_stop = 0
    x_step = 0.01

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 100000,
        "wait_time": 1.25e6,
        # "x_sweep": [10, 11],  # "predist_pulse_%d" % l for l in list(range(28, 166))
        "x_sweep": ((x_start), (x_stop + x_step / 2), (x_step)),
        # "x_sweep": [-0.1],
        "qubit_op": "gaussian_pi",
        # "flux_pulse": "constant_pulse",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        # "fetch_period": 3,
    }

    plot_parameters = {
        "xlabel": "Flux pulse amplitude",
        # "plot_type": "2D",
    }

    experiment = VacuumRabi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
