"""
A python class describing a power rabi measurement with repeated qubit pulses using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class RepPowerRabiEf(Experiment):

    name = "repeat_power_rabi_ef"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_ge_pi",  # operation used for exciting the qubit
        "qubit_ef_op",
        "fit_fn",  # fit function
        "pulse_number",
    }

    def __init__(
        self,
        qubit_ge_pi,
        qubit_ef_op,
        pulse_number,
        fit_fn="sine",
        **other_params
    ):

        self.qubit_ge_pi = qubit_ge_pi
        self.qubit_ef_op = qubit_ef_op
        self.fit_fn = fit_fn
        self.pulse_number = pulse_number

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, qubit_ef = self.modes  # get the modes
        qubit.play(self.qubit_ge_pi)
        qua.align(qubit.name, qubit_ef.name)
        for k in range(self.pulse_number):  # play qubit pulse multiple times
            qubit_ef.play(self.qubit_ef_op, ampx=self.x)
        qua.align(qubit.name, qubit_ef.name)
        qubit.play(self.qubit_ge_pi)  # e->g
        qua.align(qubit.name, rr.name, qubit_ef.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1.5
    amp_stop = 1.5
    amp_step = 0.05

    parameters = {
        "modes": ["QUBIT", "RR", "QUBIT_EF"],
        "reps": 5000,
        "wait_time": 325000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_ge_pi": "pi",
        "qubit_ef_op": "pi2",
        "pulse_number": 2,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
    }

    experiment = RepPowerRabiEf(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
