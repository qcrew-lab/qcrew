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

    name = "pi_pulse_scope"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "flux_op",
        "flux_delay",
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, flux_op, flux_delay, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.flux_op = flux_op
        self.flux_delay = flux_delay
        self.fit_fn = fit_fn
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, flux, rr = self.modes  # get the modes
        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qua.wait(self.y, qubit.name)
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.wait(int(self.flux_delay // 4), flux.name)
        flux.play(self.flux_op, ampx=0.25)
        qua.align(flux.name, rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), flux.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -200e6  # 181.25e6
    x_stop = 0e6  # 181.5e6
    x_step = 1e6

    y_start = 1  # 181.25e6
    y_stop = 200  # 181.5e6
    y_step = 2

    parameters = {
        "modes": ["QUBIT", "FLUX", "RR"],
        "reps": 2000,
        "wait_time": 80000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        "flux_delay": 60,  # ns
        "qubit_op": "constant_pi_pulse",
        "flux_op": "constant_pulse",
        "fetch_period": 5,
        # "plot_quad": "I_AVG",
        # "fit_fn": "gaussian",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "plot_type": "2D",
    }

    experiment = PiPulseScope(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
