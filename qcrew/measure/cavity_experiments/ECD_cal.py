"""
A python class describing an ECD calibration experiment, following Campagne-Ibarq et al. 2020 Quantum Error correction of a qubit encoded in a grid....
It is essentially a characteristic function (C(\beta)) measurement of the vacuum state.

NOT FINISHED
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np


# ---------------------------------- Class -------------------------------------


class ECDCalibration(Experiment):

    name = "ECD_calibration"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op1",  # operation used for exciting the qubit
        "qubit_op2",
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(
        self, cav_op, qubit_op1, qubit_op2, fit_fn="gaussian", delay=4, **other_params
    ):

        self.cav_op = cav_op
        self.qubit_op1 = qubit_op1
        self.qubit_op2 = qubit_op2
        self.fit_fn = fit_fn
        self.delay = delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes
        
        qua.reset_frame(cav.name)

        qubit.play(self.qubit_op1)  # play pi/2 pulse around X

        # start ECD gate
        qua.align()  # wait for qubit pulse to end
        cav.play(self.cav_op, ampx=self.x, phase=0)  # First positive displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_op, ampx=-self.x, phase=0)  # First negative displacement
        qua.align()
        qubit.play(self.qubit_op2)  # play pi to flip qubit around X
        qua.align()  # wait for qubit pulse to end
        cav.play(self.cav_op, ampx=-self.x, phase=0)  # Second negative displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_op, ampx=self.x, phase=0)  # Second positive displacement
        qua.align()

        qubit.play(
            self.qubit_op1,
            phase=0,
        )  # play pi/2 pulse around X or Y, to measure either the real or imaginary part of the characteristic function
        qua.align()  # align measurement
        rr.measure((self.I, self.Q))

        # wait system reset
        qua.wait(int(self.wait_time // 4))

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.8
    x_stop = 1.8
    x_step = 0.1

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 10000,
        "wait_time": 3.5e6,
        "fetch_period": 3,  # time between data fetching rounds in sec
        "delay": 50,  # pi/chi
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_op1": "constant_cos_pi2",
        "qubit_op2": "constant_cos_pi",
        "cav_op": "constant_cos_ECD",
        "plot_quad": "I_AVG",
        # "single_shot": True,
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
    }

    experiment = ECDCalibration(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
