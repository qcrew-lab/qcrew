"""
A python class describing a Jaynes Cummings PowerRabi using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Jaynes_Cummings_PowerRabi(Experiment):

    name = "jc_power_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, int(qubit.int_freq))
        qubit.play("gaussian_sel_pi_01p")
        qua.update_frequency(qubit.name, int(26.25e6))
        qubit.play("gaussian_sel_pi_1p2m")

        qua.update_frequency(qubit.name, int(67.10e6))  #
        qubit.play(self.qubit_op, ampx=self.x)  # |1+>→|2-> play qubit pulse
        # qubit.play(self.qubit_op, ampx=self.x)  # |1+>→|2-> play qubit pulse

        qua.update_frequency(qubit.name, int(26.25e6))
        qubit.play("gaussian_sel_pi_1p2m")
        qua.update_frequency(qubit.name, int(qubit.int_freq))
        qubit.play("gaussian_sel_pi_01p")

        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -1.9
    x_stop = 1.9
    x_step = 0.1

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 50000,
        "wait_time": 100000,
        "x_sweep": ((x_start), (x_stop + x_step / 2), (x_step)),
        "qubit_op": "gaussian_sel_pi_2m3p",
        # "fetch_period": 20,
        # "plot_quad": "I_AVG",
        "fit_fn": "sine",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = Jaynes_Cummings_PowerRabi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
