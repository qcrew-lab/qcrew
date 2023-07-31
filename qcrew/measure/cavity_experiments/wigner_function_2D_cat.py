"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

# from turtle import title
from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np


# ---------------------------------- Class -------------------------------------


class WignerFunction(Experiment):

    name = "wigner_function_2D_grape"

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
        delay,
        fit_fn=None,
        **other_params
    ):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.delay = delay
        self.qubit_grape = qubit_grape
        self.cav_grape = cav_grape

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)

        """State preparation"""

        # cav.play(self.cav_op, ampx=0, phase=0)

        cav.play(
            self.cav_op,  ampx = 1,
        )

        # qua.align(cav.name, qubit.name)
        qua.align()
        qubit.play("constant_cosine_pi2_pulse")
        qua.align()
        qua.wait(int(self.delay // 4))
        cav.play(
            self.cav_op,  ampx = 1,
        )
        qua.align()
        qubit.play("constant_cosine_pi_selective_pulse0")
        qua.align()
        cav.play(
            self.cav_op,  ampx = -1,
        )
        qua.align()




        # cav.play(self.cav_op)

        ## single displacement
        cav.play(
            self.cav_op,
            ampx=(self.x / 2, -self.y / 2, self.y / 2, self.x / 2),
            phase=0.5,
        )
        qua.align(cav.name, qubit.name)

        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4),
            cav.name,
            qubit.name,
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op)  # play pi/2 pulse around X

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -3
    x_stop = 3
    x_step = 0.2

    y_start = -3
    y_stop = 3
    y_step = 0.2

    # pulselist = ['grape_fock1_pulse', 'grape_fock01_pulse', 'grape_fock0-1_pulse', 'grape_fock0i1_pulse', 'grape_fock0-i1_pulse', 'vacuum', 'coh1',]



    parameters = {
        "modes": ["QUBIT", "CAVB", "RR"],
        "reps": 2000,
        "wait_time": 6000e3,
        "delay": 700,  # pi/chi
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "constant_cosine_pi2_pulse",
        "cav_op": "gaussian_coh1",
        "qubit_grape": None,
        "cav_grape": None,
        "single_shot": False,
        "plot_quad": "I_AVG",
        "fetch_period": 30,  # time between data fetching rounds in sec
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": None,
    }

    experiment = WignerFunction(**parameters)

    experiment.name = "wigner_function_" + 'cat2'
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
