"""
A python class describing a qubit readout contrast using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitReadoutContrast(Experiment):

    name = "qubit_ro_contrast"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes
        # CHOOSE PROPER QUBIT FREQ
        # qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qubit.play(self.qubit_op, ampx=self.y)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q), ampx=self.x)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 400000,
        "wait_time": 80000,
        "x_sweep": (0.6, 1.6 + 0.02 / 2, 0.02),
        "y_sweep": (0.0, 1.0),
        "qubit_op": "gaussian_pulse",
    }

    plot_parameters = {
        "xlabel": "RR amplitude",
        "trace_labels": ["no qubit pulse", "qubit pulse"],
    }

    experiment = QubitReadoutContrast(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
