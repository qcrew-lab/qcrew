from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class char_func_1D_qua_macro_ff(Experiment):

    name = "char_func_1D_qua_macro_ff"
    #with fast flux and measure real and imag
    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_state_op",
        "char_func_displacement",  # operation for displacing the cavity
        "qubit_pi",
        "qubit_pi2",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
        "measure_real",
    }

    def __init__(
        self,
        cav_state_op,
        char_func_displacement,
        qubit_pi,
        qubit_pi2,
        fit_fn="gaussian",
        delay=4,
        measure_real=True,
        **other_params,
    ):
        self.cav_state_op = cav_state_op
        self.char_func_displacement = char_func_displacement
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes
        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)

        # Bias qubit to ECD point
        # char
        flux.play("constcos20ns_tomo_RO_tomo_new_E2pF2pG2pH2_3", ampx=-0.567) #lk
        # flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0524) #hk
        
        qubit.lo_freq =5.77e9 #char
        qua.update_frequency(qubit.name, int(-176.4e6), keep_phase = True)
        qua.update_frequency(cav.name, int(-39.185e6), keep_phase = True)
        
        qua.wait(220, cav.name, qubit.name)
        with qua.switch_(self.y):
            with qua.case_(0):
                Char_2D_singledisplacement(
                    cav,
                    qubit,
                    self.char_func_displacement,
                    self.qubit_pi,
                    self.qubit_pi2,
                    0,
                    self.x,
                    delay=self.delay,
                    measure_real=self.measure_real,
                    tomo_phase=0.0,
                    correction_phase=0, #0.01595
                )
            with qua.case_(1):
                Char_2D_singledisplacement(
                    cav,
                    qubit,
                    self.char_func_displacement,
                    self.qubit_pi,
                    self.qubit_pi2,
                    0,0
                    self.x,
                    delay=self.delay,
                    measure_real=not self.measure_real,
                    tomo_phase=0.0,
                    correction_phase=0,#0.11277, #0.01595
                )
        # Measure cavity state
        # qua.wait(int(self.rr_delay // 4), rr.name, "QUBIT_EF")  # ns
        qua.wait(360, rr.name, "QUBIT_EF")
        # qua.wait(int(1400 // 4), rr.name, "QUBIT_EF")  # ns
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        # wait system reset


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.90
    x_stop = 1.91
    x_step = 0.1
    
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 1000,
        "wait_time": 1e6,
        "fetch_period": 5,  # time between data fetching rounds in sec
        "delay": 120,  # 188,  # wait time between opposite sign displacements
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (0, 1),
        "qubit_pi": "gaussian_pi_short_ecd",
        "qubit_pi2": "gaussian_pi2_short_ecd",
        "char_func_displacement": "ecd2_displacement",
        "cav_state_op": "_",
        "fit_fn": "gaussian",
        "measure_real": True,
        "single_shot": True,
        # "plot_quad": "I_AVG",  # measure real part of char function if True, imag Part if false
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        # "ylabel": "Y",
        # "plot_type": "2D",
        "cmap": "bwr",
    }

    experiment = char_func_1D_qua_macro_ff(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
