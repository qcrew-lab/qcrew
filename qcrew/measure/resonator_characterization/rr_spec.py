"""
A python class describing a readout resonator spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class RRSpectroscopy(Experiment):

    name = "rr_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, fit_fn="lorentzian", **other_params):

        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr,) = self.modes  # get the modes

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

<<<<<<< HEAD
    x_start = -55e6
    x_stop = -45e6
    x_step = 0.05e6

    parameters = {
        "modes": ["RR"],
        "reps": 6000,
=======
    x_start = -53e6
    x_stop = -47e6
    x_step = 0.1e6

    parameters = {
        "modes": ["RR"],
        "reps": 50000,
>>>>>>> 9aa82c38fe04c7565f5f6e9352cb821b7fa7507a
        "wait_time": 40000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
    }

    experiment = RRSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
