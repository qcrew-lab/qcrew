"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitSpectroscopyFastFlux(Experiment):

    name = "qubit_spec_fast_flux"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, flux, rr = self.modes  # get the modes
        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qua.wait(self.y, qubit.name)
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.wait(100, flux.name)
        flux.play("constant_pulse", ampx=-0.3)
        qua.wait(200, rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), flux.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -200e6  # 181.25e6
    x_stop = 0e6  # 181.5e6
    x_step = 1e6

    y_start = 80  # 181.25e6
    y_stop = 120  # 181.5e6
    y_step = 1

    parameters = {
        "modes": ["QUBIT", "FLUX", "RR"],
        "reps": 100000,
        "wait_time": 20000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        "qubit_op": "constant_pi_pulse",
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {"xlabel": "Qubit pulse frequency (Hz)", "plot_type": "2D"}

    experiment = QubitSpectroscopyFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
