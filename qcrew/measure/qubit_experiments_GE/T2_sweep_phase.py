"""
A python class describing a T2 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class T2(Experiment):

    name = "T2"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="exp_decay_sine", **other_params):

        self.qubit_op = qubit_op  # half pi pulse
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """

        qubit, rr, _ = self.modes  # get the modes

        qubit.play(self.qubit_op, ampx=0.1)  # play half pi qubit pulse
        ## Since there is no wait, the qubit won't decay. The sweep in phase will show
        ## stable oscillations

        qua.reset_frame(qubit.name)
        # qua.reset_frame(qubit.name)
        # qua.wait(10, qubit.name)
        qubit.play("pi", ampx=1, phase=0.25)  # This line breaks the oscillations
        # qua.wait(10, qubit.name)
        # qua.reset_frame(qubit.name)
        qubit.play(self.qubit_op, phase=self.x)  # play half pi qubit pulse
        qua.align()  # wait last qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# # -------------------------------- Execution -----------------------------------

import time

if __name__ == "__main__":
    x_start = 0
    x_stop = 1.1
    x_step = 0.03

    parameters = {
        "modes": ["QUBIT", "RR", "QUBIT_EF"],
        "reps": 5000,
        "wait_time": 100000,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_op": "pi2",
        "single_shot": True,
        # "plot_quad": "I_AVG",
        "fetch_period": 2,
    }

    plot_parameters = {
        "xlabel": "Cycle fraction",
    }

    experiment = T2(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
