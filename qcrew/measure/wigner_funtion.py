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


class Wigner_function(Experiment):

    name = "wigner_function"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",
    }

    def __init__(self, cav_op, qubit_op, fit_fn=None, delay=None,  **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.delay = delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes
        qua.reset_frame(cav.name)
        
        # TODO work in progress
        cav.play(self.cav_op, ampx=self.x, phase = 0)  # displacement in I direction
        cav.play(self.cav_op, ampx=self.y, phase = 0.25) # displacement in Q direction
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(int(self.wait_time // 4), cav.name) # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        
        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
    
    def plot(plotter, independent_data, dependent_data, n, *args, **kwargs):
        
        plotter.live_2dplot(plotter.axis[0,0], independent_data,dependent_data, n)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 50000,
        "wait_time": 600000,
        "delay": 1 ,  #np.pi / 170e3
        "x_sweep": (-1, 1, 0.05),
        "y_sweep": (-1, 1, 0.05),
        "qubit_op": "pi2",
        "cav_op": "constant_pulse",
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D"
    }

    experiment = Wigner_function(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
