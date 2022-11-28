"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar
from qcrew.control import Stagehand
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitSpectroscopy(Experiment):

    name = "qubit_spec"

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
        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qubit.play(self.qubit_op, ampx=self.y)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -200e6
    x_stop = -0e6
    x_step = 1e6

    lo_freq_list = [
        4.4e9,
        4.6e9,
        4.8e9,
        5.0e9,
        5.2e9,
        5.4e9,
        5.6e9,
        5.8e9,
        6.0e9,
        7.8e9,
        8.0e9
    ]
    for freq in lo_freq_list:
        with Stagehand() as stage:
            qubit = stage.QUBIT
            qubit.lo_freq = freq

        parameters = {
            "modes": ["QUBIT", "RR"],
            "reps": 10000,
            "wait_time": 100000,
            "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
            "y_sweep": (
                # 0.2,
                # 0.4,
                # 0.6,
                # 0.8,
                # 1.0,
                # 1.2,
                1.0,
            ),
            "qubit_op": "gaussian_pulse",
            "fit_fn": None,
            "plot_quad": "Z_AVG",
            "fetch_period": 2,
        }

        plot_parameters = {
            "xlabel": "Qubit pulse frequency (Hz)",
            # "plot_err": False
        }

        experiment = QubitSpectroscopy(**parameters)
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
