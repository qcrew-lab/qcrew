"""
A python class describing a flux pulse spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class PiPulseScope(Experiment):

    name = "rr_scope"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "flux_op",
        "flux_delay",
        "rr_delay",
        "fit_fn",  # fit function
    }

    def __init__(self, flux_op, flux_delay, fit_fn=None, **other_params):

        self.flux_op = flux_op
        self.flux_delay = flux_delay
        self.fit_fn = fit_fn
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        flux, rr = self.modes  # get the modes
        flux.play(self.flux_op, ampx=0.2)
        qua.wait(int(self.x // 4), rr.name)  # ns
        rr.measure((self.I, self.Q))  # measure transmitted signal

        qua.align()
        qua.wait(int(self.wait_time // 4), flux.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    # x_start = -150e6  # 181.25e6
    # x_stop = -50e6  # 181.5 e6
    # x_step = 1e6

    # sweep over rr delay in cc
    x_start = 1
    x_stop = 400
    x_step = 1

    parameters = {
        "modes": ["FLUX", "RR"],
        "reps": 7000,
        "wait_time": 50000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        # "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        "flux_delay": 200,  # ns
        "flux_op": "predist_square_pulse",
        "fetch_period": 15,
        # "plot_quad": "I_AVG",
        "fit_fn": "gaussian",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        # "plot_type": "2D",
    }

    experiment = PiPulseScope(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
