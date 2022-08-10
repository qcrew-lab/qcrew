"""
A python class describing a e-f qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitSpectroscopyEF(Experiment):

    name = "qubit_spec_ef"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_ef_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_ef_op, qubit_pi_pulse_name, fit_fn=None, **other_params):

        self.qubit_ef_op = qubit_ef_op
        self.fit_fn = fit_fn
        self.qubit_pi_pulse_name = qubit_pi_pulse_name

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, qubit_ef, rr = self.modes  # get the modes

        qubit.play(self.qubit_pi_pulse_name)  # g->e
        qua.align(qubit.name, qubit_ef.name)
        qua.update_frequency(qubit_ef.name, self.x)  # update to e->f (sweep variable)
        qubit_ef.play(self.qubit_ef_op)  # e->f
        qua.align(qubit.name, qubit_ef.name)
        # qua.update_frequency(qubit.name, qubit.int_freq)  # update to g->e
        qubit.play(self.qubit_pi_pulse_name)  # g->e
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -189e6
    x_stop = -184e6
    xstep = 0.05e6

    parameters = {
        "modes": ["QUBIT_ALPHA", "QUBIT_ALPHA_EF", "RR"],
        "reps": 20000,
        "wait_time": 200000,
        "x_sweep": (int(x_start), int(x_stop + xstep / 2), int(xstep)),
        "qubit_ef_op": "gaussian_pulse",
        "qubit_pi_pulse_name": "pi",
        "fit_fn": None,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = QubitSpectroscopyEF(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
