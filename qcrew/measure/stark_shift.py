"""
A python class describing a Stark shift using QM.
The experiment is essentially a qubit spectroscopy experiment with different readout powers. 
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class StarkShift(Experiment):

    name = "stark_shift"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="lorentzian", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q), ampx=self.y))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 20000,
        "wait_time": 32000,
        "x_sweep": (int(-53e6), int(-47e6 + 0.05e6 / 2), int(0.05e6)),
        "y_sweep": (0.1, 1.5 + 0.05 / 2, 0.05),
        "qubit_op": "gaussian_pulse",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "ylabel": "Resonator pulse amplitude scaling",
        "plot_type": "2D",
    }

    experiment = StarkShift(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
