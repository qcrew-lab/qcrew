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


class vacuum_rabi_predistortion_length(Experiment):

    name = "vacuum_rabi_predistortion_length"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="", **other_params):
        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        self.internal_sweep = list(np.arange(8, 41, 1))
        super().__init__(**other_params)  # Passes o4her parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be  played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        for flux_len in self.internal_sweep:
            qua.align()

            # # Fock satae preparation
            # qubit.play("gaussian_pi")
            # qua.align(qubit.name, flux.name)
            # flux.play(f"constcos6ns_reset_1to2_25ns_E2pF2pG2pH2", ampx=0.15)
            # qua.align()

            # Vacuum rabi of next transition
            qubit.play(self.qubit_op, ampx=1)  # play pi qubit pulse
            qua.align(flux.name, qubit.name)
            flux.play(f"constcos6ns_reset_1to2_{flux_len}ns_E2pF2pG2pH2", ampx=-0.23)
            qua.wait(int((200 + 3 * flux_len) // 4), rr.name)
            # qua.play("digital_pulse", "QUBIT_EF")
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

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 10000,
        "wait_time": 1.0e6,
        "qubit_op": "gaussian_pi_hk",
        # "flux_pulse": "constant_pulse",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        "fetch_period": 3,
        # "fit_fn": "sine",
    }

    plot_parameters = {
        "xlabel": "Flux pulse length (ns)",
        # "plot_type": "2D",
    }

    experiment = vacuum_rabi_predistortion_length(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
