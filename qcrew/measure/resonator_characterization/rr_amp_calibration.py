"""
A python class describing a readout pulse amplitude calibration using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class RRAmpCalibration(Experiment):

    name = "rr_amp_calibration"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
        "qubit_pi_pulse",  # well
    }

    def __init__(self, qubit_pi_pulse, fit_fn=None, **other_params):

        self.qubit_pi_pulse = qubit_pi_pulse
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        rr, qubit = self.modes  # get the modes

        qubit.play(self.qubit_pi_pulse, ampx=self.y)
        qua.align(qubit.name, rr.name)
        rr.measure((self.I, self.Q), ampx=self.x)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["RR", "QUBIT"],
        "reps": 10000,
        "wait_time": 40000,
        "qubit_pi_pulse": "pi",
        "x_sweep": (0.001, 0.12 + 0.001 / 2, 0.001),
        "y_sweep": (0.0, 1.0),
    }
    plot_parameters = {
        "xlabel": "Resonator pulse amplitude scaling",
        "ylabel": "Qubit state",
    }

    experiment = RRAmpCalibration(**parameters)
    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
