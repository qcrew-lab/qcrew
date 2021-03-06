"""
A python class describing a readout resonator spectroscopy with readout pulse amplitude
sweep using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

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
        rr, qubit = self.modes  # get the modes

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        rr.measure((self.I, self.Q), ampx=self.y)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["RR", "QUBIT"],
        "reps": 2000,
        "wait_time": 100000,
        "x_sweep": (int(-55e6), int(-49e6 + 0.3e6 / 2), int(0.3e6)),
        "y_sweep": [0.01, 0.015, 0.02],
    }
    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
        "ylabel": "Resonator pulse amplitude scaling",
        #"plot_type": "1D",
        #"zlog": True
    }

    experiment = RRSpecSweepAmplitude(**parameters)
    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
