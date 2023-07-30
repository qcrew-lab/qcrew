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


class RRSpectroscopyFastFlux(Experiment):

    name = "rr_spec_fast_flux"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
        "flux_op",
    }

    def __init__(self, flux_op, rr_delay, fit_fn=None, **other_params):

        self.fit_fn = fit_fn
        self.flux_op = flux_op
        self.rr_delay = rr_delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr, flux, qubit) = self.modes  # get the modes
        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequenc
        flux.play(self.flux_op, ampx=-0.3)
        # qua.align(qubit.name, flux.name)
        qua.wait(int(self.rr_delay // 4), qubit.name)
        qubit.play("gaussian_pi", ampx=self.y)
        qua.align(qubit.name, rr.name)
        # qua.wait(int(self.rr_delay // 4), rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -51.4e6
    x_stop = -48e6
    x_step = 0.05e6

    parameters = {
        "modes": ["RR", "FLUX", "QUBIT"],
        "reps": 20000,
        "wait_time": 60000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (0.0, 1.0),
        "rr_delay": 2500,  # ns
        # "plot_quad": "PHASE_SWEEP"
        "flux_op": "predist_square_plusminus_pulse",
        "fit_fn": "gaussian",
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
    }

    experiment = RRSpectroscopyFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
