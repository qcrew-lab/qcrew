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


class Qfunction(Experiment):

    name = "Q_function"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(self, cav_op, qubit_op, fit_fn=None, delay=4, dis = None, **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.delay = delay
        self.dis = dis

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes
        qua.reset_frame(cav.name)

        # TODO work in progress
        cav.play(self.cav_op, ampx=self.dis, phase=0)
        
    
        cav.play(self.cav_op, ampx=self.x, phase=0)  # displacement in I direction
        cav.play(self.cav_op, ampx=self.y, phase=0.25)  # displacement in Q direction
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 20000,
        "wait_time": 600000,
        "fetch_period": 4,  # time between data fetching rounds in sec
        "delay":  2941,#1666, # #2777, #2500, #2941 # pi/chi
        "x_sweep": (-1.5, 1 + 0.05 / 2, 0.05),
        "y_sweep": (-1, 1 + 0.05 / 2, 0.05),
        "qubit_op": "select_pi",
        "cav_op": "gaussian_pulse",
        "dis": 0.5,
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        #"plot_type": "1D",
        "err": False,
        
        
        
        "cmap": "bwr",
    }

    experiment = Qfunction(**parameters)
    experiment.setup_plot(**plot_parameters)
    print(experiment.modes)
    prof.run(experiment)
