from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class CharacteristicFunction1D(Experiment):

    name = "char_func_1D_qua_macro_dc"

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
        # qua.reset_frame(qubit.name)
        # qua.reset_phase(qubit.name)

        # with qua.switch_(self.y):
        #     with qua.case_(0):
        #         qua.align()
        #     with qua.case_(1):
        #         # Fock satae preparation
        #         qua.update_frequency(qubit.name, int(qubit.int_freq))
        #         qubit.play("gaussian_pi")
        #         qua.align(qubit.name, flux.name)
        #         flux.play(f"constcos6ns_reset_1to2_27ns_E2pF2pG2pH2", ampx=0.14)
        #         qua.align()
        #     with qua.case_(2):
        #         # Fock satae preparation
        #         qua.update_frequency(qubit.name, int(qubit.int_freq))
        #         qubit.play("gaussian_pi")
        #         qua.align(qubit.name, flux.name)
        #         flux.play(f"constcos6ns_reset_1to2_27ns_E2pF2pG2pH2", ampx=0.14)
        #         qua.align()
        #         # Fock satae 2 preparation
        #         qubit.play("gaussian_pi")
        #         qua.align(qubit.name, flux.name)
        #         flux.play(f"constcos2ns_reset_1to2_23ns_E2pF2pG2pH2", ampx=0.25)
        #         qua.align()

        # qua.update_frequency(qubit.name, int(-176.4e6))
        # qua.align()
        # flux.play("constcos80ns_1000ns_E2pF2pG2pH2", ampx=-0.0565)
        # qua.wait(int(120 // 4), cav.name, qubit.name)

        # qua.wait(int(160//4), cav.name, qubit.name)
        #####################  Measure the created state with charactristic function  #####################
        # this uses ampx matrixes. this somehow makes all pulses smaller by approx fac. sqrt2
        # qua.update_frequency(cav.name, int(-38.26e6), keep_phase=True)
        # with qua.switch_(self.y):
        #     with qua.case_(0):
        #         cav.play("cohstate_1_short", ampx=0)
        #     with qua.case_(1):
        #         cav.play("cohstate_1_short")
        #     with qua.case_(2):
        #         cav.play("cohstate_2_short")
        #     with qua.case_(3):
        #         cav.play("cohstate_3_short")
        #     with qua.case_(4):
        #         cav.play("cohstate_4_short")
        #     with qua.case_(5):
        #         cav.play("cohstate_5_short")
        #     with qua.case_(6):
        #         cav.play("cohstate_6_short")
        # qua.update_frequency(cav.name, cav.int_freq)
        # qua.wait(1250 * 2, cav.name)

        # Coherent state preparation
        # qua.update_frequency(cav.name, int(-38.67e6), keep_phase=True)
        # cav.play("cohstate_1_short", ampx=1)
        # qua.update_frequency(cav.name, cav.int_freq)
        # # qua.reset_frame(cav.name)
        # # qua.wait(0, cav.name)
        # # qua.align()
        # qua.wait(40, flux.name, rr.name, qubit.name, "QUBIT_EF")

        # Bias qubit to ECD point
        # flux.play("constcos20ns_tomo_RO_tomo_2_E2pF2pG2pH2", ampx=-0.121)
        # qua.wait(int((60+ 850) // 4), cav.name, qubit.name)
        ## char
        # flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2_11092023", ampx=-0.445)
        # qubit.lo_freq =5.77e9 #char
        # qua.update_frequency(qubit.name, int(-176.4e6))
        # qua.update_frequency(cav.name, int(-39.1475e6))
        # qua.wait(int(1200 // 4), cav.name, qubit.name)  # ns
        
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
                    0,
                    self.x,
                    delay=self.delay,
                    measure_real=not self.measure_real,
                    tomo_phase=0.0,
                    correction_phase=0, #0.01595
                )
        # Measure cavity state
        qua.align(rr.name, "QUBIT_EF", qubit.name)
        # qua.wait(int(100 // 4), rr.name, "QUBIT_EF")  # ns
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
    # x_start = -1.8
    # x_stop = 1.81
    # x_step = 0.1
    x_start = -1.90
    x_stop = 1.91
    x_step = 0.1
    
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 50000,
        "wait_time": 1e6,
        "fetch_period": 5,  # time between data fetching rounds in sec
        "delay": 116,  # 188,  # wait time between opposite sign displacements
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

    experiment = CharacteristicFunction1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
