"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

import numpy as np

# ---------------------------------- Class -------------------------------------


class PowerRabi2D(Experiment):

    name = "power_rabi_2D"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="sine", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        # qua.reset_frame(qubit.name)
        qubit.play(self.qubit_op, ampx=self.x, duration=self.y)

        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1.7
    amp_stop = 1.7
    amp_step = 0.05

    #     duration_start = 200
    #     duration_stop = 1000
    #     duration_step = 50

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 50000,
        "wait_time": 50000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "y_sweep": [500],  # [300 + 60*i for i in range(70)],
        "qubit_op": "pi_selective",
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        "ylabel": "sigma ",
        "plot_type": "1D",
    }

    experiment = PowerRabi2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
