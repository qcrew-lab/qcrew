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
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class ECDCalibration(Experiment):

    name = "ECD_calibration"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "ecd_displacement",  # operation for displacing the cavity
        "qubit_pi2",  # operation used for exciting the qubit
        "qubit_pi",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(
        self,
        ecd_displacement,
        qubit_pi,
        qubit_pi2,
        fit_fn="gaussian",
        delay=4,
        measure_real=True,
        **other_params
    ):

        self.ecd_displacement = ecd_displacement
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        ###################### do a first measurement  #####################

        ######################  charactristic function  1D measurement #####################
        Char_1D_singledisplacement(
            cav,
            qubit,
            self.ecd_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            ampx=self.x,
            delay=self.delay,
            measure_real=self.measure_real,
            tomo_phase=0,
        )
        # play pi/2 pulse around X or Y, to measure either the real or imaginary part of the characteristic function
        qua.align()  # align measurement
        rr.measure((self.I, self.Q))

        # wait system reset
        qua.wait(int(self.wait_time // 4))
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.7
    x_stop = 1.7
    x_step = 0.05

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR"],
        "reps": 1000,
        "wait_time": 200e3,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 500,  # pi/chi
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_pi2": "pi2",
        "qubit_pi": "pi",
        "ecd_displacement": "daddy_ecd_1",
        "single_shot": False,
        "plot_quad": "I_AVG",
        "measure_real": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {"xlabel": "X"}  # beta of (ECD(beta))

    experiment = ECDCalibration(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
