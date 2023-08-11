"""
A python class describing a readout resonator spectroscopy with readout pulse amplitude
sweep using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from cmath import phase
from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class RRSpecSweepAmplitude(Experiment):

    name = "rr_spec_sweep_amplitude"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, fit_fn=None, **other_params):

        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr,) = self.modes  # get the modes

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        rr.measure((self.I, self.Q), ampx=self.y)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 47e6
    x_stop = 52e6
    x_step = 0.2e6

    parameters = {
        "modes": ["RR"],
        "reps": 2000,
        "wait_time": 20000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": [0.2, 0.5],
        "plot_quad": "Z_AVG",
        # "plot_quad": "PHASE_SWEEP",
    }
    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
        "ylabel": "Resonator pulse amplitude scaling",
        "plot_type": "1D",
        # "zlog": True
        # "plot_err" : None,
    }

    experiment = RRSpecSweepAmplitude(**parameters)
    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
