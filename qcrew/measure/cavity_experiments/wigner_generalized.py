"""
A python class describing a generalized Wigner measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np


# ---------------------------------- Class -------------------------------------
class WignerFunction(Experiment):

    name = "Generalized_Wigner_function"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(self, cav_op, qubit_op, point, fit_fn=None, delay=4, **other_params):
        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.delay = delay
        self.point = point


        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        cav.play(self.cav_op, ampx=0, phase=0.5)  # state to be imaged


    
        
        # cav.play(self.cav_op, ampx=(self.x, -self.y, self.y, self.x), phase=0.5)
        cav.play(self.cav_op, ampx=(np.real(point), -np.imag(point), np.imag(point), np.real(point)), phase=0.5)

        


       
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4),
            cav.name,
            qubit.name,
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # Wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":


    points_list = [0.1 + 0.2j, 0.2 + 0.3j, 0.4 + 0.4j, 0.5 + 0.5j]

    for point in points_list:

        parameters = {
            "modes": ["QUBIT", "CAVB", "RR"],
            "reps": 10,
            "wait_time": 1200e3,
            "fetch_period": 4,  # time between data fetching rounds in sec
            "delay": 750,  # pi/chi for a regular Wigner
            "x_sweep": [0, 1],#(x_start, x_stop + x_step / 2, x_step),
            "point": point, 
            "qubit_op": "gaussian_pi2_pulse",
            "cav_op": "gaussian_coh1_long",
            "single_shot": False,
            "plot_quad": "I_AVG",
        }

        plot_parameters = {
            "xlabel": "X",
            "ylabel": "Y",
            "plot_type": "1D",
            "cmap": "bwr",
            "plot_err": False,
        }

        experiment = WignerFunction(**parameters)
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
