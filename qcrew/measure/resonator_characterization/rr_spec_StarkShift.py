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

    def __init__(self, fit_fn=None, **other_params):

        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr, qubit_drive) = self.modes  # get the modes

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        qua.update_frequency(qubit_drive.name, self.y)
        qubit_drive.play("constant_pulse", ampx=1.6)  # Play continuous pump
        # qua.align()
        # qua.wait(int(100000//4), rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.align()
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    amp_start = 0.0
    amp_stop = 1.6
    amp_step = 0.1

    x_start = -53e6  # -105e6#+0.1e6  #-56e6 #-41e6
    x_stop = -51e6  # -95e6#+0.1e6   #-48e6# -37e66
    x_step = 0.02e6

    y_start = -200e6  # -105e6#+0.1e6  #-56e6 #-41e6
    y_stop = -1e6  # -95e6#+0.1e6   #-48e6# -37e66
    y_step = 5e6

    parameters = {
        "modes": ["RR", "QUBIT_DRIVE"],
        "reps": 50000,
        "wait_time": 100000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        # "y_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        "fetch_period": 4,
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
        "plot_type": "2D",
    }

    experiment = RRSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
