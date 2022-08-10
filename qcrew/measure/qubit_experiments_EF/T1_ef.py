"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class T1EF(Experiment):

    name = "T1_ef"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_ge_pi",  # operation used for exciting the qubit from g to e
        "qubit_ef_pi",  # operation used for exciting the qubit from e to f
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_ge_pi, qubit_ef_pi, fit_fn="exp_decay", **other_params
    ):

        self.qubit_ge_pi = qubit_ge_pi  # pi pulse
        self.qubit_ef_pi = qubit_ef_pi  # pi pulse
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, qubit_ef, rr = self.modes  # get the modes

        qubit.play(self.qubit_ge_pi)  # g-> e pi
        qua.align(qubit.name, qubit_ef.name)
        qubit_ef.play(self.qubit_ef_pi)  # e-> f pi
        qua.wait(self.x)  # wait for partial ef decay
        qua.align(qubit.name, qubit_ef.name)
        qubit.play(self.qubit_ge_pi)  # e->g pi
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit g population
        qua.wait(int(self.wait_time //4))  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 4
    x_stop = 30e3
    x_step = 300
    

    parameters = {
        "modes": ["QUBIT", "QUBIT_EF", "RR"],
        "reps": 20000,
        "wait_time": 100000,
        "qubit_ge_pi": "constant_cos_pi",
        "qubit_ef_pi": "pi",
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "plot_quad": "I_AVG"
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = T1EF(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
