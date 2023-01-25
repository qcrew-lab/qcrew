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

    def __init__(self, fit_fn="gaussian", **other_params):

        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr, qubit) = self.modes  # get the modes

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency

        qubit.play("pi", ampx=1)  # play qubit pulse
        qua.align()  # wait qubit pulse to end
        rr.measure((self.I, self.Q), ampx=1)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

<<<<<<< Updated upstream
    x_start = -60e6  #
    x_stop = -40e6  #
    x_step = 0.05e6
    # x_start = -51e6  #
    # x_stop = -49e6  #
    # x_step = 0.02e6
=======
    x_start = -52e6  # -105e6#+0.1e6  #-56e6 #-41e6
    x_stop = -48e6  # -95e6#+0.1e6   #-48e6# -37e66
    x_step = 0.01e6
>>>>>>> Stashed changes

    parameters = {
        "modes": ["RR", "QUBIT"],
        "reps": 80000,
        "wait_time": 1000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "plot_quad": "PHASE",
        "fit_fn": "phase_atan_s",
        "cable_delay": 1.8e-6,  # in 1 / freq units
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
    }

    experiment = RRSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
