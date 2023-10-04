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


class WignerFunction(Experiment):

    name = "wigner_function"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(self, cav_op, qubit_op, rr_drive, fit_fn="gaussian", delay=4, **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.delay = delay
        self.rr_drive = rr_drive

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)

        # cav.play(self.cav_op, ampx=0.0, phase=0.0)       

        cav.play(self.cav_op, ampx=self.x, phase=0.25)  # displacement in I direction
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.align(qubit.name, rr.name)
        rr.play(self.rr_drive, duration = int(self.delay//4), ampx = 0)
        qua.align(rr.name, qubit.name)

        qubit.play(self.qubit_op)  # play pi/2 pulse around X

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        qua.wait(int(250))
        rr.measure((self.I, self.Q))  # measure transmitted signal
        
        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        # rr.play("constant_pulse", duration=5e3, ampx=1)
        # cav.play("constant_pulse", duration=5e3, ampx=0.04)
        qua.wait(int(self.wait_time // 4), cav.name)
        

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -2
    x_stop = 2
    x_step = 0.1

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 400,
        "wait_time": 10e6,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 289,  # pi/chi
        "rr_drive": "constant_drive",
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "qubit_op": "qubit_gaussian_short_pi2_pulse",
        "cav_op": "coherent_1_long",
        "fit_fn": 'gaussian',
        "single_shot": True,
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "1D",
        "cmap": "bwr",
    }

    experiment = WignerFunction(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
