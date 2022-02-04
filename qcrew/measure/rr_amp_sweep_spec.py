"""
A python class describing a readout resonator spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class RRAmpSpectroscopy(Experiment):

    name = "rr_amp_sweep_spec"

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

        qua.update_frequency(rr.name, -50e6)  # update resonator pulse frequency
        qubit.play("pi", ampx=self.y)
        qua.align(rr.name,qubit.name)
        rr.measure((self.I, self.Q), ampx=self.x)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["RR", "QUBIT"],
        "reps": 30000,
        "wait_time": 40000,
        #"x_sweep": (int(), int( +  / 2), int())
        "x_sweep": (0.05, 0.2 + 0.005 / 2, 0.005),
        "y_sweep": [0.0, 1.0],
    }
    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
        "ylabel": "Resonator pulse amplitude scaling",
        "plot_type": "1D",
    }

    experiment = RRAmpSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
