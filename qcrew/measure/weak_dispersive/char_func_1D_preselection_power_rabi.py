from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class char_func_1D_preselection_power_rabi(Experiment):

    name = "char_func_1D_preselection_power_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_state_op",
        "char_func_displacement",  # operation for displacing the cavity
        "qubit_pi",
        "qubit_pi2",  # operation used for exciting the qubit
        "corrected_phase",
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
        corrected_phase, 
        fit_fn="gaussian",
        delay=4,
        measure_real=True,
        **other_params,
    ):
        self.cav_state_op = cav_state_op
        self.char_func_displacement = char_func_displacement
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.corrected_phase = corrected_phase
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux, qubit_lk = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)

        # Coherent state preparation and evolution
        if 0: # low kerr evolution
            qubit.lo_freq = 5.1937e9  
            qua.update_frequency(cav.name, int(-39.21e6), keep_phase=True)
            qua.update_frequency(qubit.name, int(-50e6), keep_phase=True)
            cav.play("cohstate_5_short_lk", ampx=0)
        if 0: #high kerr evolution
            qubit.lo_freq = 5.77e9 
            qua.update_frequency(cav.name, int(-38.67e6), keep_phase=True)
            qua.update_frequency(qubit.name, int(-93.19e6), keep_phase=True)
            cav.play("cohstate_5_short_hk", ampx=0)
        if 1: ## rr
            qubit.lo_freq = 5.77e9 
            qua.update_frequency(cav.name, int(-38.67e6), keep_phase=True)
            qua.update_frequency(qubit.name, int(-131.1e6), keep_phase=True)
            cav.play("cohstate_5_short_hk", ampx=0)    

        # qua.wait(10, flux.name)
        qua.align(cav.name, qubit.name)
        qubit.play("gaussian_pi_rr", ampx=0)
        qua.wait(200, qubit.name)
        qubit.play("gaussian_pi_rr", ampx=0)
        qua.wait(200, qubit.name)
        qubit.play("gaussian_pi_rr", ampx=0)
        qua.wait(200, qubit.name)
        qubit.play("gaussian_pi_rr", ampx=0)
        qua.wait(200, qubit.name)
        qubit.play("gaussian_pi_rr", ampx=0)
        qua.wait(200, qubit.name)
        qubit.play("gaussian_pi_rr", ampx=self.x)

        # char
        # qubit.lo_freq = 5.77e9  # char
        qua.update_frequency(qubit.name, int(-176.4e6), keep_phase=True)
        qua.update_frequency(cav.name, int(-39.185e6), keep_phase=True)

        qua.align()

        # Bias qubit to ECD point
        # flux.play("constcos80ns_tomo_RO_3_E2pF2pG2pH2", ampx=0.03645)
        # qua.wait(25, cav.name, qubit.name)
        if 0:
            flux.play("constcos20ns_tomo_RO_tomo_new_E2pF2pG2pH2_3", ampx=-0.5685) # lk
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.1) #rr
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0524) #hk 

        # Preselection
        # qua.wait(int(30 // 4), rr.name, "QUBIT_EF")  # ns
        # qua.play("digital_pulse", "QUBIT_EF")
        # rr.measure((self.I, self.Q))  # measure transmitted signal=
        
        qua.update_frequency(qubit_lk.name, int(-250e6), keep_phase=True)
        qua.play("digital_pulse", qubit_lk.name)
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        qua.wait(int(970 // 4), cav.name, qubit.name)

        ######################  Measure the created state with charactristic function  #####################
        # this uses ampx matrixes. this somehow makes all pulses smaller by approx fac. sqrt2
        Char_2D_singledisplacement_double_rr(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            0,
            0,
            delay=self.delay,
            measure_real=self.measure_real,
            tomo_phase=0,
            correction_phase=self.corrected_phase,  # 0.01595
        )

        # Measure qubit state
        # qua.align(rr.name, "QUBIT_EF", qubit.name)
        # qua.wait(int(20 // 4), rr.name, "QUBIT_EF")  # ns
        # qua.play("digital_pulse", "QUBIT_EF")
        # rr.measure((self.I, self.Q))  # measure transmitted signal
        
        qua.update_frequency(qubit_lk.name, int(-250e6), keep_phase=True)
        qua.align(rr.name, qubit_lk.name, qubit.name)
        qua.wait(int(20 // 4), rr.name, qubit_lk.name)  # ns
        qua.play("digital_pulse", qubit_lk.name)
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.90
    x_stop = 1.91
    x_step = 0.1

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX", "QUBIT_LK"],
        "reps": 10000,  # 25000
        "wait_time": 80000,
        "fetch_period": 20,  # time between data fetching rounds in sec
        "delay": 120,  # 188,  # wait time between opposite sign displacements
        "corrected_phase": 0, 
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        # "y_sweep": (0, 1),
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
        "skip_plot": True,
    }

    experiment = char_func_1D_preselection_power_rabi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
