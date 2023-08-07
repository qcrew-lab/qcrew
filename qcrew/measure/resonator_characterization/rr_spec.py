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
        (rr,) = self.modes  # get the modes
        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequenc
        # cav.play("const_cohstate_1", ampx=self.y)  # play displacement to cavity
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -53.0e6
    x_stop = -47.0e6
    x_step = 0.25e6

    parameters = {
        "modes": [
            "RR",
        ],
        "reps": 200000,
        "wait_time": 20000,  # 500ns*5 = 2.5us = 2500ns
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        # "y_sweep":[0.,1.],
        # "y_sweep": (0.0, ),#0.5, 1.0, 1.5),
        # "plot_quad": "PHASE_SWEEP",
        "fit_fn": "gaussian",
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
    }

    experiment = RRSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
