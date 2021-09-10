"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class NSplitBSweepSpec(Experiment):

    name = "number_split_b_sweep_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, cav_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        cav.play(self.cav_op, ampx=self.y)  # prepare cavity state
        qua.align(cav.name, qubit.name)  # align modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 3000000,
        "wait_time": 600000,
        "x_sweep": (int(-50.9e6), int(-49.6e6 + 25e3 / 2), int(25e3)),
        "y_sweep": (0, 0.182, 0.182 * 2 ** 0.5),
        "qubit_op": "select_pi",
        "cav_op": "constant_pulse",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "trace_labels": ["<n> = 0", "<n> = 1", "<n> = 2"],
    }

    experiment = NSplitBSweepSpec(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
