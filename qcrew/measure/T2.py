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
        "detuning",  # qubit pulse detuning
    }

    def __init__(self, qubit_op, detuning=0, fit_fn="exp_decay_sine", **other_params):

        self.qubit_op = qubit_op  # half pi pulse
        self.fit_fn = fit_fn
        self.detuning = detuning  # frequency detuning of qubit operation

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq + self.detuning)  # detune
        qubit.play(self.qubit_op)  # play half pi qubit pulse
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qubit.play(self.qubit_op)  # play half pi qubit pulse
        qua.align(qubit.name, rr.name)  # wait last qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 2000000,
        "wait_time": 32000,
        "x_sweep": (int(16), int(700 + 12 / 2), int(12)),
        "qubit_op": "pi2",
        "detuning": int(700e3),
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = T2(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
