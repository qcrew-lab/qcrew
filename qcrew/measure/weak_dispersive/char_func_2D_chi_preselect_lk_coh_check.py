from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class char_func_2D_chi_preselect_lk_coh(Experiment):

    name = "char_func_2D_chi_preselect_lk_coh"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_state_op",
        "char_func_displacement",  # operation for displacing the cavity
        "qubit_pi",
        "qubit_pi2",  # operation used for exciting the qubit
        "qubit_evolution",
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
        qubit_evolution,
        corrected_phase,
        fit_fn=None,
        delay=4,
        measure_real=True,
        **other_params,
    ):
        self.cav_state_op = cav_state_op
        self.char_func_displacement = char_func_displacement
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.qubit_evolution = qubit_evolution
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
        qua.reset_frame(qubit_lk.name)

        # Coherent state preparation and evolution
        if 1:  # low chi evolution
            # qubit.lo_freq = 5.1937e9
            qua.update_frequency(cav.name, int(-39.251e6), keep_phase=True)  # -39.21e6
            qua.update_frequency(qubit_lk.name, int(-50e6), keep_phase=True)
            cav.play("cohstate_2dot5_short_lk", ampx=0.5)
        if 0:  # high chi evolution
            # qubit.lo_freq = 5.77e9
            qua.update_frequency(cav.name, int(-38.67e6), keep_phase=True)
            qua.update_frequency(qubit.name, int(-93.19e6), keep_phase=True)
            cav.play("cohstate_2dot5_short_hk", ampx=1)
        # qua.wait(10, flux.name)  #
        qua.align()
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)
        # qubit_lk.play(self.qubit_evolution, ampx=0)
        # qua.wait(int(400 // 4), qubit_lk.name)

        # char
        # qubit.lo_freq = 5.77e9  # char
        qua.update_frequency(qubit.name, int(-176.4e6), keep_phase=True)
        qua.update_frequency(cav.name, int(-39.185e6), keep_phase=True)

        # qua.wait(200, qubit.name)
        # qua.wait(1250 * 2, cav.name)
        qua.align()

        # Bias qubit to ECD point
        # flux.play("constcos80ns_tomo_RO_3_E2pF2pG2pH2", ampx=0.03645)
        # qua.wait(25, cav.name, qubit.name)

        # Bias qubit to ECD point

        if 1:
            flux.play("constcos20ns_tomo_RO_tomo_new_E2pF2pG2pH2_3", ampx=-0.5675)  # lk
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.1)  # rr
        if 0:  ####
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0527)  # hk

        # Preselection
        qua.update_frequency(qubit_lk.name, int(250e6), keep_phase=True)
        qua.wait(int(30 // 4), rr.name, qubit_lk.name)  # ns
        qua.play("digital_pulse" * qua.amp(0.0), qubit_lk.name)
        rr.measure((self.I, self.Q), ampx=0)  # measure transmitted signal=

        # if self.single_shot:  # assign state to G or E
        #     qua.assign(
        #         self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
        #     )

        # self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        qua.wait(int(970 // 4), cav.name, qubit.name)

        ######################  Measure the created state with charactristic function  #####################
        # this uses ampx matrixes. this somehow makes all pulses smaller by approx fac. sqrt2
        Char_2D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            self.x,
            self.y,
            delay=self.delay,
            measure_real=self.measure_real,
            tomo_phase=0,
            correction_phase=self.corrected_phase,  # 0.01595
        )

        # Measure qubit state
        qua.align(rr.name, qubit_lk.name, qubit.name)
        qua.wait(int(20 // 4), rr.name, qubit_lk.name)  # ns
        qua.play("digital_pulse", qubit_lk.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
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

    y_start = -1.9
    y_stop = 1.91
    y_step = 0.1

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX", "QUBIT_LK"],
        "reps": 400,
        "wait_time": 1e6,
        "fetch_period": 60,  # time between data fetching rounds in sec
        "delay": 116,  # wait time between opposite sign displacements
        "corrected_phase": 0.577821,
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_pi": "gaussian_pi_short_ecd",
        "qubit_pi2": "gaussian_pi2_short_ecd",
        "qubit_evolution": "gaussian_pi2_lk",
        "char_func_displacement": "ecd2_displacement",
        "cav_state_op": "_",
        "measure_real": True,
        "single_shot": True,
        # "plot_quad": "I_AVG",  # measure real part of char function if True, imag Part if false
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        # "skip_plot": True,
    }

    experiment = char_func_2D_chi_preselect_lk_coh(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
