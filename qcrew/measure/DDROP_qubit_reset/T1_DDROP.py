"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class T1DDROP(Experiment):

    name = "T1_DDROP"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="exp_decay", **other_params):

        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn

        self.steady_state_wait = 500
        self.rr_ddrop_freq = int(-49.7e6)
        self.qubit_ddrop = "ddrop_pulse"
        self.rr_ddrop = "ddrop_pulse"

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qubit.play(self.qubit_op)  # play pi qubit pulse
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        # qua.wait(int(self.steady_state_wait // 4), qubit.name)  # wait rr reset
        # qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        # qua.update_frequency(rr.name, self.rr_ddrop_freq)
        # rr.play(self.rr_ddrop)  # play rr ddrop excitation
        # qua.wait(int(self.steady_state_wait // 4), qubit.name)  # wait rr reset
        # qubit.play(self.qubit_ddrop)  # play qubit ddrop excitation

        # qua.update_frequency(rr.name, rr.int_freq)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 4
    x_stop = 30e3
    x_step = 300

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 20000,
        "wait_time": 100000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "pi",
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = T1DDROP(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
