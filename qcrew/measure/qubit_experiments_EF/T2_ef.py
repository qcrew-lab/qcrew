"""
A python class describing a T2 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class T2EF(Experiment):

    name = "T2_ef"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_ge_pi",  # operation used for exciting the qubit from g to e
        "qubit_ef_pi2",  # half-ppi operation between e and f
        "detuning",  # qubit pulse detuning
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_ge_pi,
        qubit_ef_pi2,
        detuning=0,
        fit_fn="exp_decay_sine",
        **other_params
    ):

        self.qubit_ge_pi = qubit_ge_pi  # pi pulse g->e
        self.qubit_ef_pi2 = qubit_ef_pi2  # pi/2 pulse e->f
        self.detuning = detuning  # frequency detuning of qubit operation
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, qubit_ef = self.modes  # get the modes
        qubit.play(self.qubit_ge_pi)  # g-> e pi

        qua.align(qubit.name, qubit_ef.name)
        qua.update_frequency(qubit_ef.name, qubit_ef.int_freq + self.detuning)
        qubit_ef.play(self.qubit_ef_pi2)  # e-> f half pi
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qubit_ef.play(self.qubit_ef_pi2)  # e-> f half pi
        qua.align(qubit.name, qubit_ef.name)

        qubit.play(self.qubit_ge_pi)  # e->g pi
        qua.align(qubit.name, rr.name)  # wait last qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 4
    x_stop = 5000
    x_step = 40
    detuning = 0e6

    parameters = {
        "modes": ["QUBIT_ALPHA", "RR"],
        "reps": 25000,
        "wait_time": 200000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_ge_pi": "pi",
        "qubit_ef_pi2": "pi2_ef",
        "ef_int_freq": int(-186.5e6),
        "detuning": int(detuning),
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = T2EF(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
