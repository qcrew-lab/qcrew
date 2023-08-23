"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

import numpy as np

# ---------------------------------- Class -------------------------------------


class Ramseyrevival(Experiment):

    name = "ramsey_revival"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, rr_delay, qubit_delay, cav_op, fit_fn=None, **other_params
    ):

        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.fit_fn = fit_fn
        self.rr_delay = rr_delay
        self.qubit_delay = qubit_delay
        # self.internal_sweep = np.arange(4, 300, 8)

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes
        qua.reset_frame()
        # prepare cavity state
        # for flux_len in self.internal_sweep:
        flux_len = 396
        qua.wait(int(440 // 4), cav.name)

        cav.play(self.cav_op, ampx=1 * 0)  # prepare cavity state
        qua.align(cav.name, qubit.name)  # align modes
        qubit.play(self.qubit_op, ampx=1)  # play qubit pulse
        qua.align()
        flux.play(f"square_{flux_len}ns_ApBpC", ampx=self.y)  # to make off resonance

        qua.wait(int((flux_len + 60) // 4), qubit.name)
        qubit.play(self.qubit_op, ampx=1.0, phase=self.x)  # play  qubit pulse with piA/2
        qua.align(qubit.name, rr.name)
        # qua.wait(int(2000 // 4), rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 4
    x_stop = 300
    x_step = 4

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 2000,
        "wait_time": 80e3,  # 1e6,
        "x_sweep": (0.0, 1.91, 0.05),
        "y_sweep": (0.412, 0.206),
        "qubit_op": "gaussian_pi2_short",
        "cav_op": "cohstate_1",
        # "single_shot": True,
        "fetch_period": 1,
        "plot_quad": "I_AVG",
        "qubit_delay": 120,  # ns
        "rr_delay": 520,  # ns
        "fit_fn": "sine",
    }

    plot_parameters = {
        "xlabel": "Wait time (ns)",
    }

    experiment = Ramseyrevival(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
