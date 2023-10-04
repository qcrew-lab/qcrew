"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np


# ---------------------------------- Class -------------------------------------


class PhaseEstimation(Experiment):
    name = "phase_estimation"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(
        self,
        cav_op,
        qubit_op,
        qubit_grape,
        cav_grape,
        qubit_grape_2,
        cav_grape_2,
        fit_fn=None,
        delay=4,
        **other_params
    ):
        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.delay = delay
        self.qubit_grape = qubit_grape
        self.cav_grape = cav_grape
        self.qubit_grape_2 = qubit_grape_2
        self.cav_grape_2 = cav_grape_2

        self.internal_sweep = ["first", "second"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)

        """State preparation"""

        qubit.play(self.qubit_grape, ampx=1)  # ampx = 0,
        cav.play(self.cav_grape, ampx=1)  # ampx = 0,

        qua.align(cav.name, qubit.name)

        """phase encoding"""

        qua.wait(self.x, cav.name, qubit.name)

        """reverse process"""

        qubit.play(self.qubit_grape_2, ampx=1)  # ampx = 0,
        cav.play(self.cav_grape_2, ampx=1)  # ampx = 0,

        if 1:
            """first projection"""
            # projection on |g>

            qua.align()  # align measurement
            rr.measure((self.I, self.Q))  # measure transmitted signal

            if self.single_shot:  # assign state to G or E
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
                )
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)

            qua.wait(int(200))
            qua.align()

            """second projection"""
            # projection on |g, vac>
            # qubit.play("qubit_gaussian_sig250ns_pi_pulse")
            qubit.play(self.qubit_op)

        qua.align()

        # qubit.play(self.qubit_op)
        # qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 1
    x_stop = 100  # clock cycle
    x_step = 2

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 300,
        "wait_time": 10e6,
        "fetch_period": 10,  # time between data fetching rounds in sec
        "x_sweep": (
            int(x_start),
            int(x_stop + x_step / 2),
            int(x_step),
        ),  # ampitude sweep of the displacement pulses in the ECD
        "qubit_op": "qubit_gaussian_sig250ns_pi_pulse",
        "cav_op": "gaussian_coh1",
        "qubit_grape": "0_plus_03alpha1947",
        "cav_grape": "0_plus_03alpha1947",
        "qubit_grape_2": "0_plus_03alpha1947_to_vac",
        "cav_grape_2": "0_plus_03alpha1947_to_vac",
        "single_shot": True,
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "wait time (clock cycle)",
        "ylabel": "probability",
        "plot_type": "1D",
        "cmap": "bwr",
        "skip_plot": False,
        "plot_err": False,
    }

    experiment = PhaseEstimation(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
