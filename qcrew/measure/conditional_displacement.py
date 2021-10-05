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


class conditiondis(Experiment):

    name = "conditional_dis"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op1",  # operation used for exciting the qubit
        "qubit_op2",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op1, qubit_op2, fit_fn=None, delay1=None, delay2=None, dis1 = None, dis2=None, dis3=None, dis4=None, **other_params):

        self.cav_op = cav_op
        self.dis1 = dis1
        self.dis2 = dis2
        self.dis3 = dis3
        self.dis4 = dis4
        self.qubit_op1 = qubit_op1
        self.qubit_op2 = qubit_op2
        self.fit_fn = fit_fn
        self.delay1 = delay1
        self.delay2 = delay2
        

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes
        qua.reset_frame(cav.name)

        # TODO work in progress
        
        # prepared |a>|g>+|-a>|e> state
        cav.play(self.cav_op, ampx=self.dis1, phase=0)
        qua.wait(self.delay1, cav.name)
        cav.play(self.cav_op, ampx=self.dis2, phase=0) 
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op1) # pi pulse
        qua.align(qubit.name, cav.name)
        cav.play(self.cav_op, ampx=self.dis3, phase=0)
        qua.wait(self.delay2, cav.name)
        cav.play(self.cav_op, ampx=self.dis4, phase=0)
        
        
        
        # Q function measurement
        cav.play(self.cav_op, ampx=self.x, phase=0)  # displacement in I direction
        cav.play(self.cav_op, ampx=self.y, phase=0.25)  # displacement in Q direction
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op2)  # selectived pi pulse
        
    

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
        "x_sweep": (-1, 1 + 0.05 / 2, 0.05),
        "y_sweep": (-1, 1 + 0.05 / 2, 0.05),
        "qubit_op1": "pi",
        "qubit_op2": "select_pi",
        "cav_op": "gaussian_pulse",
        "dis1": 0.5,
        "dis2": -0.5,
        "dis3": -0.5,
        "dis4": 0.5,
        "delay1": 125, # clock
        "delay2": 125, # clock
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "err": False,
        "cmap": "bwr",
    }

    experiment = conditiondis(**parameters)
    experiment.setup_plot(**plot_parameters)
    print(experiment.modes)
    prof.run(experiment)
