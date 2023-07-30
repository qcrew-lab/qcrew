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


class FLUXPI(Experiment):

    name = "flux_pi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="", **other_params):
        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        # self.flux_pulse = flux_pulse
        self.internal_sweep = np.arange(4, 100, 4) #list(np.arange(4, 100, 4))
        super().__init__(**other_params)  # Passes other parameters to parent
    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        for length in self.internal_sweep:
            flux.play(f"castle_{length}", ampx=0.24)  # to make off resonance -80e6
            qua.wait(int((252) // 4), rr.name, qubit.name, flux.name)  # ns
            qubit.play(self.qubit_op)  # play pi qubit pulse
            qua.wait(int((380+length) // 4), rr.name)
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

    # y_start = 1 #cc
    # y_stop = 100 #cc
    # y_step = 1

    # x_start = -0.1
    # x_stop = 0
    # x_step = 0.05

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 100000,
        "wait_time": 1.25e6,
        # "x_sweep": ((x_start), (x_stop + x_step / 2), (x_step)),
        # "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        # "x_sweep": [-0.1],
        "qubit_op": "gaussian_pi",
        # "flux_pulse": "constant_pulse",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        "fetch_period": 2,
    }

    plot_parameters = {
        "xlabel": "wait time (ns)",
        # "plot_type": "2D",
    }

    experiment = FLUXPI(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
