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

    name = "wigner_function_superposition"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(self, cav_op, qubit_op1, qubit_op2, fit_fn=None, delay=4, cav_amp1 = None, cav_amp2 = None, **other_params):

        self.cav_op = cav_op
        self.qubit_op1 = qubit_op1
        self.qubit_op2 = qubit_op2
        self.fit_fn = fit_fn
        self.delay = delay
        self.cav_amp1 = cav_amp1
        self.cav_amp1 = cav_amp2

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes
        qua.reset_frame(cav.name)
        
        

        # TODO work in progress
        
        # Prepare state (|0>+|1>)/sqrt(2)
        cav.play(self.cav_op, ampx = self.cav_amp1)
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op1, qubit.name)
        qua.align(qubit.name, cav.name)
        cav.play(self.cav_op, ampx = self.cav_amp2)
        
        # displace state
        cav.play(self.cav_op, ampx=self.x, phase=0)  # displacement in I direction
        cav.play(self.cav_op, ampx=self.y, phase=0.25)  # displacement in Q direction
        
        # parity measurement 
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op2)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4), cav.name
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op2)  # play pi/2 pulse around X

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
        "reps": 13298,
        "wait_time": 600000,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay":  2777, #2500, #2941 # pi/chi
        "x_sweep": (-1, 1 + 0.05 / 2, 0.05),
        "y_sweep": (-1, 1 + 0.05 / 2, 0.05),
        "qubit_op1": "select_pi",
        "qubit_op2": "pi2",
        "cav_op": "constant_pulse",
        "cav_amp1": 0.56 * 0.257,
        "cav_amp2": -0.24 * 0.257 * ,
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "err": False,
        
        
        
        "cmap": "bwr",
    }

    experiment = WignerFunction(**parameters)
    experiment.setup_plot(**plot_parameters)
    print(experiment.modes)
    prof.run(experiment)
