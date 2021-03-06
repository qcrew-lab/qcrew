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
        "cav_op_ecd", # fixed displacement. 
        "cav_op_qfunc", # displacement with varying amp to sweep phase space
        "qubit_op1_ecd", # pi2 pulse
        "qubit_op2_ecd", # pi pulse
        "qubit_op_qfunc", # conditional pi pulse
        "ecd_amp_scale", # amp scaling factor for cav_op_ecd pulse
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(
        self,
        cav_op_qfunc,
        cav_op_ecd,
        qubit_op_qfunc,
        qubit_op1_ecd,
        qubit_op2_ecd,
        ecd_amp_scale,
        fit_fn=None,
        delay=4,
        measure_real=True,
        
        **other_params
    ):
        self.cav_op_qfunc = cav_op_qfunc
        self.cav_op_ecd = cav_op_ecd
        self.qubit_op_qfunc = qubit_op_qfunc
        self.qubit_op1_ecd = qubit_op1_ecd
        self.qubit_op2_ecd = qubit_op2_ecd
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real
        self.ecd_amp_scale = ecd_amp_scale

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes
        
        
        # one iteration of the squeezing protcol
        
        # Initialize the qubit in a supersposition state
        qubit.play(self.qubit_op1_ecd)
        #ECD Gate
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_op_ecd, ampx=self.ecd_amp_scale, phase=0)  # First positive displacement
        qua.wait(int(self.delay // 4), cav.name) # wait time between opposite sign displacements
        cav.play(self.cav_op_ecd, ampx=-self.ecd_amp_scale, phase=0)  # First negative displacement
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_op2_ecd)  # pi pulse to flip the qubit state (echo)
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_op_ecd, ampx=-self.ecd_amp_scale, phase=0)  # Second negative displacement
        qua.wait(int(self.delay // 4), cav.name) # wait time between opposite sign displacements
        cav.play(self.cav_op_ecd, ampx=self.ecd_amp_scale, phase=0)  # Second positive displacement
        qua.align(qubit.name, cav.name)
        
        # final pi2 pulse to end the squeezing sequence
        qubit.play(self.qubit_op1_ecd)
        
        
        # Measure the created state with the qfunc
        cav.play(self.cav_op_qfunc, ampx=self.x, phase=0)  # displacement in I direction
        cav.play(self.cav_op_qfunc, ampx=self.y, phase=0.25)  # displacement in Q direction
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_qfunc)  # play qubit selective pi-pulse
        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
# -------------------------------- Execution -----------------------------------
for i in [0.125, 0.25, 0.75, 1.5, 2]:
    if __name__ == "__main__":
        x_start = -1.4
        x_stop = 1.4
        x_step = 0.1

        y_start = -1.4
        y_stop = 1.4
        y_step = 0.1
        
        ecd_amp_scale = i
        print(ecd_amp_scale)

        parameters = {
            "modes": ["QUBIT", "CAV", "RR"],
            "reps": 30000,
            "wait_time": 100000,
            "fetch_period": 8,  # time between data fetching rounds in sec
            "delay": 500,  # wait time between opposite sign displacements
            "ecd_amp_scale" : ecd_amp_scale,
            "x_sweep": (x_start, x_stop + x_step / 2, x_step),  # ampitude sweep of the displacement pulses in the ECD
            "y_sweep": (y_start, y_stop + y_step / 2, y_step),
            "qubit_op1_ecd": "pi2",
            "qubit_op2_ecd": "pi", 
            "qubit_op_qfunc": "pi_selective",
            "cav_op_ecd": "CD_cali",
            "cav_op_qfunc": "cohstate_1",
        
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
