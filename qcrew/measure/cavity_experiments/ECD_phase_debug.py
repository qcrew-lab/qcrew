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


class ECDPhaseDebug(Experiment):

    name = "ECD_Phase_Debug"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",# operation for displacing the cavity
        "cav_coh",
        "qubit_op_ecd1",  # operation used for exciting the qubit
        "qubit_op_ecd2",# operation used for exciting the qubit
        "qubit_op_meas",
        "fit_fn",  # fit function
        "delay",
        "ecd_amp_scale", # amp scaling factor for cav_op_ecd pulse
        "cav_coh_amp_scale"
        # describe...
    }

    def __init__(
        self, cav_op,cav_coh, qubit_op_ecd1, qubit_op_ecd2, qubit_op_meas, ecd_amp_scale, cav_coh_amp_scale, fit_fn="sine", delay=4, **other_params
    ):

        self.cav_op = cav_op
        self.cav_coh = cav_coh
        self.qubit_op_ecd1 = qubit_op_ecd1
        self.qubit_op_ecd2 = qubit_op_ecd2
        self.qubit_op_meas = qubit_op_meas
        self.fit_fn = fit_fn
        self.delay = delay
        self.ecd_amp_scale = ecd_amp_scale
        self.cav_coh_amp_scale = cav_coh_amp_scale
        
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes
        qua.reset_frame(cav.name)

        
        #qubit.play(self.qubit_op_ecd2)  # play pi/2 pulse around X

        # ECD gate
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_op, ampx=self.ecd_amp_scale, phase=0)  # First positive displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_op, ampx=-self.ecd_amp_scale, phase=0)  # First negative displacement
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_op_ecd2)  # play pi to flip qubit around X
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_op, ampx=-self.ecd_amp_scale, phase=0)  # Second negative displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_op, ampx=self.ecd_amp_scale, phase=0)  # Second positive displacement
        
        #bring qubit back
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_op_ecd2)
        qua.align(qubit.name, cav.name)
        # qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        # cav.play(self.cav_op, ampx=self.ecd_amp_scale, phase=0)  # First positive displacement
        # qua.wait(int(self.delay // 4), cav.name)
        # cav.play(self.cav_op, ampx=-self.ecd_amp_scale, phase=0)  # First negative displacement
        # qua.align(qubit.name, cav.name)
        # qubit.play(self.qubit_op_ecd2)#   play pi to flip qubit around X
        # qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        # cav.play(self.cav_op, ampx=-self.ecd_amp_scale, phase=0)  # Second negative displacement
        # qua.wait(int(self.delay // 4), cav.name)
        # cav.play(self.cav_op, ampx=self.ecd_amp_scale, phase=0)  # Second positive displacement
        # qua.align(qubit.name, cav.name)
        # qubit.play(self.qubit_op_ecd2)
        # qua.align(qubit.name, cav.name)
        
        # cavity displacement with approx same amplitude as ECD which phase we sweep
        #cav.play(self.cav_coh, ampx = cav_coh_amp_scale, phase=0.25)
        cav.play(self.cav_coh, ampx = self.x, phase=0.74)

        
        # measurement sequence
        qua.align(cav.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op_meas)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align all modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    ecd_amp_scale = 2.4
    cav_coh_amp_scale = 1.5
    x_start = 0.1
    x_stop = 2
    x_step = 0.01

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 100000,
        "wait_time": 2000000,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 300,  # pi/chi
        "cav_coh_amp_scale" : cav_coh_amp_scale,
        "ecd_amp_scale" : ecd_amp_scale,
        "x_sweep": (x_start,x_stop + x_step / 2, x_step), # phase = x*2pi
        "qubit_op_ecd1": "constant_cos_pi2",
        "qubit_op_ecd2": "constant_cos_pi",
        "qubit_op_meas": "pi_selective1",
        "cav_op": "constant_cos_ECD",
        "cav_coh": "constant_cos_cohstate_1",
    }

    plot_parameters = {
        "xlabel": "X",  # phase of coherent state creaetd by 
    }

    experiment = ECDPhaseDebug(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
