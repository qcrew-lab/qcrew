"""
This script follows Fig S4 from Quantum error correction of a qubit encoded in grid states of an oscillator
A. Eickbusch et al.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np


# ---------------------------------- Class -------------------------------------


class CavityDisplacementCalBerry(Experiment):

    name = "cavity_displacement_cal_berry"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_disp",
        "cav_disp_ecd",  # operation for displacing the cavity
        "qubit_op1",
        "qubit_op2",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
        "measure_real",
    }

    def __init__(
        self,
        cav_disp,
        cav_disp_ecd,
        qubit_op1,
        qubit_op2,
        fit_fn=None,
        delay=4,
        measure_real=True,
        **other_params
    ):
        self.cav_disp = cav_disp
        self.cav_disp_ecd = cav_disp_ecd
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
        
      
        qua.reset_frame(cav.name)
        
        # Bring qubit into superpositon
        qubit.play(self.qubit_op1)
        
        # Do the first ECD gate
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_disp_ecd, ampx=self.x, phase=0)  # First positive displacement
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        cav.play(self.cav_disp_ecd, ampx=-1*self.x, phase=0)  # First negative displacement
        qua.align(qubit.name, cav.name)
        qubit.play('pi')  # play pi to flip qubit around X
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_disp_ecd, ampx=-1*self.x, phase=0)  # Second negative displacement
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        cav.play(self.cav_disp_ecd, ampx=self.x, phase=0)  # Second positive displacement
        qua.align(qubit.name, cav.name)
        
        # Do the first displacement 
        cav.play(self.cav_disp, ampx=self.x, phase=0.25)
        
        # Do the second ECD gate
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_disp_ecd, ampx=self.x, phase=0.5)  # First positive displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_disp_ecd, ampx=-self.x, phase=0.5)  # First negative displacement
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_op2)  # play pi to flip qubit around X
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_disp_ecd, ampx=-self.x, phase=0.5)  # Second negative displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_disp_ecd, ampx=self.x, phase=0.5)  # Second positive displacement
        qua.align(qubit.name, cav.name)
        
        # Do the second displacement 
        cav.play(self.cav_disp, ampx=self.x, phase=0.75)
        
        ###
        # Do the third ECD gate
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_disp_ecd, ampx=self.x, phase=0.5)  # First positive displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_disp_ecd, ampx=-self.x, phase=0.5)  # First negative displacement
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_op2)  # play pi to flip qubit around X
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_disp_ecd, ampx=-self.x, phase=0.5)  # Second negative displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_disp_ecd, ampx=self.x, phase=0.5)  # Second positive displacement
        qua.align(qubit.name, cav.name)
        
        # Do the fourth displacement 
        cav.play(self.cav_disp, ampx=self.x, phase=0.25)
        
        # Do the fifth ECD gate
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_disp_ecd, ampx=self.x, phase=0.5)  # First positive displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_disp_ecd, ampx=-self.x, phase=0.5)  # First negative displacement
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_op2)  # play pi to flip qubit around X
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_disp_ecd, ampx=-self.x, phase=0.5)  # Second negative displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_disp_ecd, ampx=self.x, phase=0.5)  # Second positive displacement
        qua.align(qubit.name, cav.name)
        ###
        
        
        
        
        # prepare sigmax measurement
        qubit.play(self.qubit_op1)
        
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.5
    x_stop = 1.5
    x_step = 0.015

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 1000000,
        "wait_time": 600000,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 500,  # wait time between opposite sign displacements
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "qubit_op1": "pi2",
        "qubit_op2": "pi",
        "cav_disp": "cohstate_1",
        "cav_disp_ecd": "CD_cali",
        # "ECD_phase": 0
        "measure_real": True,  # measure real part of char function if True, imag Part if false
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
    }

    experiment = CavityDisplacementCalBerry(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
