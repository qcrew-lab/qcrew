"""
A python class describing a ef power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class PowerRabiEF(Experiment):

    name = "power_rabi_ef"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_ef_op",  # operation used for exciting the qubit
        "qubit_ge_pi",
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_ef_op, qubit_ge_pi, fit_fn="sine", **other_params):

        self.qubit_ef_op = qubit_ef_op
        self.qubit_ge_pi = qubit_ge_pi
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, qubit_ef, rr = self.modes  # get the modes

        qubit.play(self.qubit_ge_pi)  # g-> e
        qua.align(qubit.name, qubit_ef.name)
        qubit_ef.play(self.qubit_ef_op, ampx=self.x)  # e-> f
        qua.align(qubit.name, qubit_ef.name)
        qubit.play(self.qubit_ge_pi)  # e->g
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    amp_start = -1.5
    amp_stop = 1.5
    amp_step = 0.01

    parameters = {
        "modes": ["QUBIT", "QUBIT_EF", "RR"],
        "reps": 3000,
        "wait_time": 100000,
        "qubit_ge_pi": "pi",
        "qubit_ef_op": "gaussian_pulse",
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
    }

    experiment = PowerRabiEF(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
