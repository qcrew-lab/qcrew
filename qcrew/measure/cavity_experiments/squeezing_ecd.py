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


class SqueezingECD(Experiment):

    name = "squeezing_ecd"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_state_op",
        "cav_op",  # operation for displacing the cavity
        "qubit_op1",
        "qubit_op2",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
        "measure_real",
    }

    def __init__(
        self,
        cav_state_op,
        cav_op,
        qubit_op1,
        qubit_op2,
        fit_fn=None,
        delay=4,
        measure_real=True,
        **other_params
    ):
        self.cav_state_op = cav_state_op
        self.cav_op = cav_op
        self.qubit_op1 = qubit_op1
        self.qubit_op2 = qubit_op2
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes
        
        
        # one iteration of the squeezing protcol
        
        # Initialize the qubit in a supersposition state
        qubit.play(self.qubit_op1)
        #ECD Gate
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_op, ampx=self.x, phase=0)  # First positive displacement
        cav.play(self.cav_op, ampx=self.y, phase=0.25)
        
       # qua.reset_frame(cav.name)
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_op, ampx=-self.x, phase=0)  # First negative displacement
        cav.play(self.cav_op, ampx=-self.y, phase=0.25)
        
        #qua.reset_frame(cav.name)
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_op2)  # play pi to flip qubit around X
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_op, ampx=-self.x, phase=0)  # Second negative displacement
        cav.play(self.cav_op, ampx=-self.y, phase=0.25)
        
        #qua.reset_frame(cav.name)
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_op, ampx=self.x, phase=0)  # Second positive displacement
        cav.play(self.cav_op, ampx=self.y, phase=0.25)
        
        # final pi2 pulse to end the squeezing sequence
        qubit.play(self.qubit_op1)
        
        
        
        
        # Measure the created state with the qfunc
        cav.play(self.cav_op, ampx=self.x, phase=0)  # displacement in I direction
        cav.play(self.cav_op, ampx=self.y, phase=0.25)  # displacement in Q direction
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op)  # play qubit selective pi-pulse
        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        
        
        

        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.5 *0.5
    x_stop =  1.5 *0.5
    x_step = 0.05
    
    y_start = -1.5 * 0.5
    y_stop =  1.5 * 0.5
    y_step = 0.05


    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 1000000,
        "wait_time": 100000,
        "fetch_period": 8,  # time between data fetching rounds in sec
        "delay": 500,  # wait time between opposite sign displacements
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op_ECD": "pi2",
        "qubit_op_qfunc": "pi_selective",
        "cav_state_op": "cohstate_2",
        "cav_op": "CD_cali",
        "measure_real": True,  # measure real part of char function if True, imag Part if false
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
                "cmap": "bwr",
    }

    experiment = SqueezingECD(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
