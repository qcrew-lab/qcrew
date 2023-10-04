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
class WignerFunction2DTwoGrape(Experiment):
    name = "wigner_function_2D_two_grape"
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

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)

        """State preparation"""

        # First pulse
        qubit.play(
            self.qubit_grape,
            ampx=0.95,
        )
        cav.play(
            self.cav_grape,
            ampx=0.95,
        )

        # Second pulse
        # qua.align(cav.name, qubit.name)
        # qubit.play(
        #     self.qubit_grape_2,
        #     ampx=0.95,
        # )
        # cav.play(
        #     self.cav_grape_2,
        #     ampx=0.95,
        # )

        if 0:
            # projection on |g>

            qua.align()  # align measurement
            rr.measure((self.I, self.Q))  # measure transmitted signal
            qua.wait(int(200))
            qua.align()

        if 0:
            qua.wait(int(600))  # keep the same length  as rr
            qua.wait(int(200))
            qua.align()

        """Measurement"""

        qua.align(cav.name, qubit.name)

        ## single displacement
        cav.play(self.cav_op, ampx=(self.x, self.y, -self.y, self.x), phase=0.32)
        qua.align(cav.name, qubit.name)

        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4),
            cav.name,
            qubit.name,
        )
        qubit.play(self.qubit_op)  # play pi/2 pulse around X

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
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
    x_start = -1.8
    x_stop = 1.8
    x_step = 0.1

    y_start = -1.8
    y_stop = 1.8
    y_step = 0.1

    # fock1
    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 55,
        "wait_time": 10e6,
        "fetch_period": 10,  # time between data fetching rounds in sec
        "delay": 289,  # pi/chi
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "qubit_gaussian_64ns_pi2_pulse",
        "cav_op": "coherent_1_long",
        "qubit_grape": "0_plus_03alpha1947",
        "cav_grape": "0_plus_03alpha1947",
        "qubit_grape_2": "0_plus_03alpha1947_to_vac",
        "cav_grape_2": "0_plus_03alpha1947_to_vac",
        "single_shot": True,
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": None,
    }

    experiment = WignerFunction2DTwoGrape(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
