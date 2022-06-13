"""
A python class describing a ef power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class QubitPopulation(Experiment):

    name = "qubit_population"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_ge_pi",
        "qubit_ef_pi",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_ge_pi, qubit_ef_pi, fit_fn="sine", **other_params
    ):

        self.qubit_ge_pi = qubit_ge_pi
        self.fit_fn = fit_fn
        self.qubit_ef_pi = qubit_ef_pi

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, qubit_ef, rr = self.modes  # get the modes

        qubit.play(self.qubit_ge_pi, ampx=self.y)
        qua.align(qubit.name, qubit_ef.name)
        qubit_ef.play(self.qubit_ef_pi, ampx=self.x)  # e-> f
        qua.align(qubit.name, qubit_ef.name)
        qubit.play(self.qubit_ge_pi)  # e-> f
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "QUBIT_EF", "RR"],
        "reps": 5000,
        "wait_time": 300000,
        "qubit_ge_pi": "pi",
        "qubit_ef_pi": "pi",
        "x_sweep": (-1.8, 1.8 + 0.1 / 2, 0.1),
        "y_sweep": [1.0],
    }

    plot_parameters = {"xlabel": "Qubit pulse amplitude scaling"}

    experiment = QubitPopulation(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
