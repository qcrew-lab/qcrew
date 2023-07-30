"""
A python class describing a vacuum rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

import numpy as np

# ---------------------------------- Class -------------------------------------
# delete this comment


class VacuumRabi2D(Experiment):

    name = "vacuum_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="", **other_params):
        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        self.internal_sweep = list(np.arange(60, 400, 8))
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        for flux_len in self.internal_sweep:
            qua.align()
            qubit.play(self.qubit_op)  # play pi qubit pulse
            qua.align(flux.name, qubit.name)
            flux.play(f"IIR_square_0726_on_time_{flux_len}", ampx=self.x)
            qua.wait(int((250 + flux_len) // 4), rr.name)  # cc
            rr.measure((self.I, self.Q))  # measure qubit state
            if self.single_shot:  # assign state to G or E7
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )
            qua.wait(int(self.wait_time // 4))  # wait system reset
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -0.5
    x_stop = -0.1
    x_step = 0.01

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 20000,
        "wait_time": 1.25e6,
        "x_sweep": ((x_start), (x_stop + x_step / 2), (x_step)),
        "qubit_op": "gaussian_pi",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        "fetch_period": 60,
    }

    plot_parameters = {
        "xlabel": "Amp of Fast Flux",
        "ylabel": "Flux_len (ns)",
        "plot_type": "2D",
    }

    experiment = VacuumRabi2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
