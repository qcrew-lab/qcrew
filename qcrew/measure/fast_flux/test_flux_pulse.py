"""
A python class describing a vacuum rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------
# delete this comment


class VacuumRabi(Experiment):

    name = "vacuum_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, flux_pulse, fit_fn="exp_decay", **other_params):

        self.fit_fn = fit_fn
        self.flux_pulse = flux_pulse

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes

        flux.play(self.flux_pulse, ampx=self.x)  # tune qubit f and wait
        qua.align(flux.name, rr.name)  # wait flux pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 0.0
    x_stop = 1.0
    x_step = 0.1

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 100000,
        "wait_time": 100000,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "flux_pulse": "predist_pulse",
        "single_shot": False,
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = VacuumRabi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
