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
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, qubit_pi_pulse_name, ef_int_freq, fit_fn="sine", **other_params
    ):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.qubit_pi_pulse_name = qubit_pi_pulse_name
        self.ef_int_freq = ef_int_freq

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qubit.play(self.qubit_pi_pulse_name)  # g-> e
        qua.update_frequency(qubit.name, self.ef_int_freq)
        qubit.play(self.qubit_op, ampx=self.x)  # e-> f
        qua.update_frequency(qubit.name, qubit.int_freq)
        qubit.play(self.qubit_pi_pulse_name)  # e->g
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 10000,
        "wait_time": 300000,
        "ef_int_freq": -87.7e6,
        "qubit_pi_pulse_name": "pi",
        "x_sweep": (-1.8, 1.8 + 0.1 / 2, 0.1),
        "qubit_op": "gaussian_pulse",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
    }

    experiment = PowerRabiEF(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
