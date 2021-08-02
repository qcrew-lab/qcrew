"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar

from qcrew.control import professor as prof
import qcrew.measure.qua_macros as macros
from qcrew.measure.experiment import Experiment

from qm import qua


# ---------------------------------- Class -------------------------------------


class ResonatorSpectroscopy(Experiment):

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "mode_names",  # names of the modes used in the experiment
        "fit_fn",  # Fit function
    }

    def __init__(self, modes, fit_fn="lorentzian", **other_params):

        self.mode_names = modes  # mode names for saving metadata
        self.modes = modes  # is updated with mode objects by the professor
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

        macros.stream_results(self.var_list)  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["RR"],
        "reps": 20000,
        "wait_time": 10000,
        "x_sweep": (int(-50e6), int(50e6 + 0.2e6 / 2), int(0.2e6)),
    }

    experiment = ResonatorSpectroscopy(**parameters)
    prof.run(experiment)
