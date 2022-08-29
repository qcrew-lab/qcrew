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

from qcrew.measure.qua_macros import ECD, Char_1D, U, V


# ---------------------------------- Class -------------------------------------


class ECDchar1D(Experiment):

    name = "ECD_char_1D"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "char_func_displacement",  # fixed displacement.
        "cav_ecd_displace",
        "u_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "qubit_pi2",  # operation used for exciting the qubit
        "qubit_pi",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(
        self,
        char_func_displacement,
        cav_ecd_displace,
        u_amp_scale,
        qubit_pi,
        qubit_pi2,
        delay,
        fit_fn="gaussian",
        measure_real=True,
        **other_params
    ):

        self.char_func_displacement = char_func_displacement
        self.cav_ecd_displace = cav_ecd_displace
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real 
        self.u_amp_scale = u_amp_scale

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        
        # state creation
        #cav.play("constant_cos_cohstate_1", phase=0.25)
        if 1:

            U(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.u_amp_scale,
                delay=self.delay,
            )     
        if 1:

            U(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.u_amp_scale,
                delay=self.delay,
            )                   
                            
        # Measure 1D char func
        Char_1D(
                cav,
                qubit,
                self.char_func_displacement,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.x,
                delay=self.delay,
                phase=0.5,
                measure_real=self.measure_real,
        )
        # play pi/2 pulse around X or Y, to measure either the real or imaginary part of the characteristic function
        qua.align()  # align measurement
        rr.measure((self.I, self.Q))

        # wait system reset
        qua.wait(int(self.wait_time // 4))
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.5
    x_stop = 0.5
    x_step = 0.05
    u_amp_scale = 0.5
    

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 1000,
        "wait_time": 4e6,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 50,  # pi/chi
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_pi2": "constant_cos_pi2",
        "qubit_pi": "constant_cos_pi",
        "char_func_displacement": "constant_cos_ECD_2",
        "cav_ecd_displace": "constant_cos_ECD",
        "single_shot": False,
        "plot_quad": "I_AVG",
        "measure_real": True,
        "u_amp_scale": u_amp_scale
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
    }


    experiment = ECDchar1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
