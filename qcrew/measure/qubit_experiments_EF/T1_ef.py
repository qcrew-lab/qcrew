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
        "ef_int_freq",  # intermediate frequency of the ef transition
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_ge_pi, qubit_ef_pi, ef_int_freq, fit_fn="exp_decay", **other_params
    ):

        self.qubit_ge_pi = qubit_ge_pi  # pi pulse
        self.qubit_ef_pi = qubit_ef_pi  # pi pulse
        self.ef_int_freq = ef_int_freq  # pi pulse
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qubit.play(self.qubit_ge_pi)  # g-> e pi
        qua.update_frequency(qubit.name, self.ef_int_freq)
        qubit.play(self.qubit_ef_pi)  # e-> f pi
        qua.wait(self.x, qubit.name)  # wait for partial ef decay
        qua.update_frequency(qubit.name, qubit.int_freq)
        qubit.play(self.qubit_ge_pi)  # e->g pi
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit g population
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 4
    x_stop = 20e3
    x_step = 300

    parameters = {
        "modes": ["QUBIT_ALPHA", "RR"],
        "reps": 25000,
        "wait_time": 100000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_ge_pi": "pi",
        "qubit_ef_pi": "pi_ef",
        "ef_int_freq": int(-186.5e6),
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = T1EF(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
