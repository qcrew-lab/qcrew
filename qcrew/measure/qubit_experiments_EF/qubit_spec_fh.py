"""
A python class describing a e-f qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitSpectroscopyFG(Experiment):

    name = "qubit_spec_fh"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",
        "qubit_ef_op",  # operation used for exciting the qubit
        "qubit_fh_op",
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_fh_op, qubit_ef_op, qubit_op, fit_fn=None, **other_params):

        self.fit_fn = fit_fn
        self.qubit_op = qubit_op
        self.qubit_ef_op = qubit_ef_op
        self.qubit_fh_op = qubit_fh_op

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, qubit_ef, qubit_fh, rr = self.modes  # get the modes

        qubit.play(self.qubit_op)  # g->e
        qua.align(qubit.name, qubit_ef.name)
        
        qubit_ef.play(self.qubit_ef_op)  # e->f
        qua.align(qubit_ef.name, qubit_fh.name)
        
        qua.update_frequency(qubit_fh.name, self.x)  # update to e->f (sweep variable)
        qubit_fh.play(self.qubit_fh_op)  # f->g
        
        qua.align(qubit_fh.name, qubit_ef.name)
        # qua.update_frequency(qubit.name, qubit.int_freq)  # update to g->e
        qubit_ef.play(self.qubit_ef_op)  # f->e
        qua.align(qubit_ef.name, qubit.name)  # wait qubit pulse to end
        qubit.play(self.qubit_op)  # e->g
        
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 90e6
    x_stop = 130e6
    xstep = 0.2e6


    parameters = {
        "modes": ["QUBIT", "QUBIT_EF", "QUBIT_FH", "RR"],
        "reps": 20000,
        "wait_time": 200000,
        "x_sweep": (int(x_start), int(x_stop + xstep / 2), int(xstep)),
        "qubit_ef_op": "gaussian_pi_pulse_ef",
        "qubit_op": "gaussian_pi_pulse",
        "qubit_fh_op": "gaussian_pi_pulse",
        "fit_fn": "gaussian",
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = QubitSpectroscopyFG(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
