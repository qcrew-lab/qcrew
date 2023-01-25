"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

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
        qubit, rr, cav = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        # cav.play('constant_cos_cohstate_1', ampx=self.y)
        qubit.play(self.qubit_op, ampx=1)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
<<<<<<< Updated upstream
    x_start = -60e6  # 45e6
    x_stop = -50e6  # 55e6
    x_step = 0.1e6

    parameters = {
        "modes": ["QUBIT", "RR", "CAV"],
        "reps": 10000,
        "wait_time": 80e3,  # 80e3,  # 80000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        # "y_sweep": [0.0, 1, 1.5],
        "qubit_op": "pi",
        "plot_quad": "I_AVG",
        "fetch_period": 2,
=======
    x_start = -64e6
    x_stop = -61e6
    x_step = 0.04e6

    with Stagehand() as stage:
        qubit = stage.QUBIT
        # qubit.lo_freq = freq

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 20000,
        "wait_time": 40000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (
            1.0,
        ),
        "qubit_op": "constant_pi_pulse3",
        "fit_fn": "gaussian",
        "plot_quad": "Z_AVG",
        "fetch_period": 1,
>>>>>>> Stashed changes
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
<<<<<<< Updated upstream
=======
        # "plot_err": False
>>>>>>> Stashed changes
    }

    experiment = QubitSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
