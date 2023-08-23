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


class FLUXPI2D(Experiment):

    name = "flux_pi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, flux_pulse, fit_fn="", **other_params):
        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        self.flux_pulse = flux_pulse
        # self.internal_sweep = [200]
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        for len in self.internal_sweep:
        if 1:
            flux.play(
                "predist_constcos_10ns_rpad_10000ns_396ns", ampx=self.x
            )  # to make off resonance
            qua.wait(int((120) // 4), rr.name, qubit.name)  # ns
            qubit.play(self.qubit_op)  # play pi qubit pulse
            qua.wait(self.y, rr.name)
            qua.wait(int((396) // 4), rr.name)
        if 0:  # castle
            flux.play(self.flux_pulse, duration=99, ampx=0.265)  # to make off resonance
            qua.wait(int((120) // 4), rr.name, qubit.name)  # ns
            qubit.play(self.qubit_op)  # play pi qubit pulse -109e6
            flux.play(
                self.flux_pulse, duration=self.y, ampx=self.x
            )  # to make on resonance
            qua.wait(self.y + int((120 + 200) // 4), rr.name)
            flux.play(
                self.flux_pulse, duration=1500, ampx=0.265
            )  # to make off resonance
            qua.wait(int((120) // 4), rr.name)

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

    y_start = 1  # cc
    y_stop = 200  # cc
    y_step = 1

    x_start = -0.15
    x_stop = 0.15
    x_step = 0.01

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 2000,
        "wait_time": 1.25e6,
        "x_sweep": ((x_start), (x_stop + x_step / 2), (x_step)),
        "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        # "x_sweep": [-0.1],
        "qubit_op": "gaussian_pi",
        "flux_pulse": "constant_pulse",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        "fetch_period": 120,
    }

    plot_parameters = {
        "xlabel": "flux pulse amp",
        "ylabel": "wait time (cc)",
        "plot_type": "2D",
    }

    experiment = FLUXPI2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
