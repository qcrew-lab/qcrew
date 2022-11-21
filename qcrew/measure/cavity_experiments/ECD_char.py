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
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class ECD_char(Experiment):

    name = "ECD_char"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "char_func_displacement",  # fixed displacement.
        "cav_ecd_displace",
        "cav_ecd_displace_special",
        # "cat_cav_ecd_displace",
        "qubit_pi",  # pi pulse
        "qubit_pi2",  # pi/2
        "u1_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v1_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u2_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v2_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u3_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v3_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u_cat_amp_scale",
        "fit_fn",  # fit function
        "delay",  # describe...
        "cav_displace_1",
        "ecd_amp_scale",
        # "rotation_time",
    }

    def __init__(
        self,
        char_func_displacement,
        cav_displace_1,
        qubit_pi,
        qubit_pi2,
        u1_amp_scale,
        v1_amp_scale,
        u2_amp_scale,
        v2_amp_scale,
        u3_amp_scale,
        v3_amp_scale,
        u_cat_amp_scale,
        cav_ecd_displace,
        cav_ecd_displace_special,
        # cat_cav_ecd_displace,
        ecd_amp_scale,
        # rotation_time,
        measure_real,
        fit_fn=None,
        delay=4,
        **other_params
    ):
        self.char_func_displacement = char_func_displacement
        self.cav_ecd_displace = cav_ecd_displace
        self.cav_ecd_displace_special = cav_ecd_displace_special
        # self.cat_cav_ecd_displace = cat_cav_ecd_displace
        self.cav_displace_1 = cav_displace_1
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real
        self.u1_amp_scale = u1_amp_scale
        self.v1_amp_scale = v1_amp_scale
        self.u2_amp_scale = u2_amp_scale
        self.v2_amp_scale = v2_amp_scale
        self.u3_amp_scale = u3_amp_scale
        self.v3_amp_scale = v3_amp_scale
        self.u_cat_amp_scale = u_cat_amp_scale
        self.ecd_amp_scale = ecd_amp_scale
        # self.rotation_time = rotation_time
        # self.internal_sweep = ["first", "second", "third"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name, qubit.name)
        qua.reset_phase(qubit.name)
        # qua.reset_phase(test.name)

        if 0:
            qua.align()
            rr.measure((self.I, self.Q))  # measure transmitted signal
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()  # align measurement
            qua.wait(int(20))
            qua.align()

        if 0:
            qua.align()
            # qubit.play(self.qubit_pi, phase=0)
            qua.align(cav.name, qubit.name)
            cav.play(self.cav_displace_1, phase=0, ampx=1)
            # qua.wait(int(400))
            qua.align()
            # qubit.play(self.qubit_op2_ecd, phase=0)

        if 0:
            qubit.play(self.qubit_pi, phase=0.25)  # play pi to flip qubit around X
            qua.align()
            # ECD Gate
            ECD(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                ampx=self.ecd_amp_scale,
                phase=0,
                delay=self.delay,
                qubit_phase=0.25,
            )

            qua.align()

        if 1:

            U(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.u1_amp_scale,
                delay=self.delay,
            )

        if 1:
            V(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.v1_amp_scale,
                delay=self.delay,
            )

        if 1:
            U(
                cav,
                qubit,
                self.cav_ecd_displace_special,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.u2_amp_scale,
                delay=self.delay,
            )
        if 1:
            V(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.v2_amp_scale,
                delay=self.delay,
            )
        if 1:
            U(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.u3_amp_scale,
                delay=self.delay,
            )
        if 1:
            V(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.v3_amp_scale,
                delay=self.delay,
            )

        if 0:
            V_cat(
                cav,
                qubit,
                self.cat_cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.u_cat_amp_scale,
                delay=self.delay,
                qubit_phase=0.25,
            )

        ###################### do a first measurement  #####################
        if 0:
            qua.align()
            rr.measure((self.I, self.Q))  # measure transmitted signal
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()  # align measurement
            qua.wait(int(20))

        ###################### decay the cat state  #####################
        qua.align()  # align measurement

        ######################  Measure the created state with charactristic function  #####################
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
        )

        # Measure cavity state
        qua.align()  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.wait(int(self.wait_time // 4))


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":

    # rotation_time_list = [16, 800, 1600]  # [16]   # [20000, 30000, 40000, 50000]

    # for n in range(len(rotation_time_list)):

    x_start = -1.2  # -1.4
    x_stop = 1.2
    x_step = 0.08

    y_start = -1.2
    y_stop = 1.2
    y_step = 0.08

    #### one UV (1, -0.6)
    #### two UV   (1.938, 0.44), (-0.572, -1.06)
    #### three UV (-0.845,  0.613),  (2.6368,  0.30), (-0.91, -0.80)

    sq3db_coeffs = [
        1.38744578,
        0.51199234,
        -0.19874056,
        -0.46461027,
        -0.3244084,
        -0.65943663,
    ]

    sq6db_coeffs = [
        -0.57844852,
        0.60452584,
        -2.15238317,
        -0.30349575,
        0.67163186,
        0.88878487,
    ]

    sq4db_coeffs = [
        -0.68959406,
        0.71339159,
        0.46450709,
        -0.45146261,
        0.77048704,
        -0.34444093,
    ]
    coeffs = sq4db_coeffs

    u_cat_amp_scale = 1.95

    ecd_amp_scale = 1

    # rotation_time = rotation_time_list[n]

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 50,
        "wait_time": 2e6,  # 50e3,
        "fetch_period": 4,  # time between data fetching rounds in sec
        "delay": 80,  # 160,  # 100# wait time between opposite sign displacements
        "u1_amp_scale": coeffs[0],
        "v1_amp_scale": coeffs[1],
        "u2_amp_scale": coeffs[2],
        "v2_amp_scale": coeffs[3],
        "u3_amp_scale": coeffs[4],
        "v3_amp_scale": coeffs[5],
        "ecd_amp_scale": ecd_amp_scale,
        "u_cat_amp_scale": u_cat_amp_scale,
        # "rotation_time": rotation_time,
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_pi2": "pi2",
        "qubit_pi": "pi",
        "char_func_displacement": "constant_cos_ECD_3",
        "cav_ecd_displace": "constant_cos_ECD_1",
        "cav_ecd_displace_special": "constant_cos_ECD_2",
        "cav_displace_1": "constant_cos_cohstate_1",
        "measure_real": True,
        "plot_quad": "I_AVG",
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": False,
        "skip_plot": False,
    }

    experiment = ECD_char(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
