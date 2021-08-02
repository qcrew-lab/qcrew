"""
A python class describing a readout resonator spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
# --------------------------------- Imports ------------------------------------
from qm import qua

from qcrew.helpers.parametrizer import Parametrized
from typing import ClassVar
from qcrew.measure.Experiment import Experiment
from qcrew.control import Stagehand
import qua_macros as macros

# ---------------------------------- Class -------------------------------------


class RRSpectroscopy(Experiment):

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "mode_names",  # names of the modes used in the experiment
        "fit_fn",  # fit function
    }

    def __init__(self, modes, fit_fn="lorentzian", **other_params):

        self.mode_names = modes  # mode names for saving metadata
        self.modes = None  # is updated with mode objects by the professor
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
        "modes": ("RR",),
        "reps": 20000,
        "wait_time": 10000,
        "x_sweep": (int(-50e6), int(50e6 + 0.2e6 / 2), int(0.2e6)),
    }

    experiment = RRSpectroscopy(**parameters)

    # The following will be done by the professor
    with Stagehand() as stage:

        mode_tuple = tuple()
        for mode_name in experiment.mode_names:
            mode_tuple += (getattr(stage, mode_name),)

        experiment.modes = mode_tuple

        power_rabi = experiment.QUA_sequence()

        #################   RUN MEASUREMENT   ##################

        job = stage.QM.execute(power_rabi)
