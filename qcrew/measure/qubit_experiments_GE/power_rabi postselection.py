"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import qcrew.measure.qua_macros as macros

# ---------------------------------- Class -------------------------------------


class PowerRabi(Experiment):
    name = "power_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="sine", **other_params):
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        self.internal_sweep = ["first", "second"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        qubit.play(self.qubit_op, ampx=self.x)
        qubit.play(self.qubit_op, ampx=self.x)

        """first projection"""
        # # projection on |g>

        qua.align()  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        qua.align()
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        qua.wait(int(150))

        " second measurement"

        qua.align()  # wait qubit pulse to end
        rr.measure((self.I, self.Q))

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    amp_start = -0.8
    amp_stop = 0.8
    amp_step = 0.02

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 1000,
        "wait_time": 500e3,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "qubit_gaussian_short_pi_pulse",
        "single_shot": True,
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "skip_plot": True
        # "zlimits": (0.35, 0.5)
    }

    experiment = PowerRabi(**parameters)
    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
