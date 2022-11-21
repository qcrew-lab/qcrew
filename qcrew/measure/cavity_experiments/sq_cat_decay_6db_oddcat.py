"""
6db sq cat
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class sq_cat_decay_6db_oddcat(Experiment):

    name = "sq_vcat_6db_oddcat"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "char_func_displacement",  # fixed displacement.
        "cav_ecd_displace",
        "cav_ecd_displace_special",
        "cat_cav_ecd_displace",
        "qubit_pi",  # pi pulse
        "qubit_pi2",  # pi/2
        "u1_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v1_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u2_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v2_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u3_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v3_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v_cat_amp_scale",
        "fit_fn",  # fit function
        "delay",  # describe...
        "cav_displace_1",
        "decay_time",
        "tomo_phase",
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
        v_cat_amp_scale,
        cav_ecd_displace,
        cav_ecd_displace_special,
        cat_cav_ecd_displace,
        decay_time,
        tomo_phase,
        measure_real,
        fit_fn=None,
        delay=4,
        **other_params
    ):
        self.char_func_displacement = char_func_displacement
        self.cav_ecd_displace = cav_ecd_displace
        self.cav_ecd_displace_special = cav_ecd_displace_special
        self.cat_cav_ecd_displace = cat_cav_ecd_displace
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
        self.v_cat_amp_scale = v_cat_amp_scale
        self.decay_time = decay_time
        self.tomo_phase = tomo_phase
        self.internal_sweep = ["first", "second", "third"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name, qubit.name)
        qua.reset_phase(qubit.name)

        if 1:
            rr.measure((self.I, self.Q))  # measure transmitted signal
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()  # align measurement
            qua.wait(int(80))
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
                self.cav_ecd_displace,
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

        if 1:
            V(
                cav,
                qubit,
                self.cat_cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.v_cat_amp_scale,
                delay=self.delay,
            )
        qua.align()
        qubit.play(self.qubit_pi)  # remove this if creating even cat
        qua.align()
        cav.play("constant_cos_cohstate_1", ampx=-0.019, phase=0.25)
        ###################### do a first measurement  #####################
        qua.align()
        rr.measure((self.I, self.Q))  # measure transmitted signal
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()  # align measurement
        qua.wait(int(80))

        ###################### decay the cat state  #####################

        qua.wait(int(self.decay_time // 4))  ###### decay time

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
            tomo_phase=self.tomo_phase,  # -0.193049,
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

    sq6db_coeffs = [
        1.62946677,
        0.39181981,
        -0.48019506,
        -1.04030892,
        -1.10939512,
        0.32484321,
    ]
    coeffs = sq6db_coeffs
    v_cat_amp_scale = 0.60142  # # 0.9021370205290902*2/3

    # tomo_phase_list = [-0.17195806, -0.13887576, -0.08391143, -0.21217849, -0.07661771, -0.21118821, -0.16405136, -0.1608981, -0.16764681]
    # tomo_phase_list =  [-0.17195806+0.01077,
    #     -0.13887576 -0.142687,
    #     -0.08391143 -0.26373,
    #     -0.21217849 + 0.0086455,
    #     -0.07661771 +0.00296,
    #     -0.21118821 + 0.00469,
    #     -0.16405136 -0.27336,
    #     -0.1608981 -0.14113832,
    #     -0.16764681]

    # tomo_phase_list = [
    #     -0.17195806 + 0.01077 + 0.0002288,
    #     -0.13887576 - 0.142687 + 0.00908,
    #     -0.08391143 - 0.26373 + 0.00686,
    #     -0.21217849 + 0.0086455 + 0.0025,
    #     -0.07661771 + 0.00296 + 0.007836,
    #     -0.21118821 + 0.00469 + 0.00862,
    #     -0.16405136 - 0.27336 + 0.01958,
    #     -0.1608981 - 0.14113832 + 0.0317,
    #     -0.16764681 + 0.02339,
    # ]
    # tomo_phase_list = [
    #     -0.17195806 + 0.01077 + 0.0002288 + 0.0002288,
    #     -0.13887576 - 0.142687 + 0.00908 + 0.00908,
    #     -0.08391143 - 0.26373 + 0.00686 + 0.00686,
    #     -0.21217849 + 0.0086455 + 0.0025 + 0.0025,
    #     -0.07661771 + 0.00296 + 0.007836 + 0.007836,
    #     -0.21118821 + 0.00469 + 0.00862 + 0.00862,
    #     -0.16405136 - 0.27336 + 0.01958 + 0.01958,
    #     -0.1608981 - 0.14113832 + 0.0317 + 0.0317,
    #     -0.16764681 + 0.02339 + 0.02339,
    # ]

    tomo_phase_list = [
        # -0.17195806 + 0.01077 + 0.0002288 + 0.0002288,
        # -0.13887576 - 0.142687 + 0.00908 + 0.00908 -0.01219892,
        # -0.08391143 - 0.26373 + 0.00686 + 0.00686 - 0.01244935,
        # -0.21217849 + 0.0086455 + 0.0025 + 0.0025,
        # -0.07661771 + 0.00296 + 0.007836 + 0.007836,
        # -0.21118821 + 0.00469 + 0.00862 + 0.00862 - 0.01520052,
        # -0.16405136 - 0.27336 + 0.01958 + 0.01958 - 0.01682689,
        # -0.1608981 - 0.14113832 + 0.0317 + 0.0317 - 0.03137782,
        -0.16764681
        + 0.02339
        + 0.02339
        - 0.01212014,
    ]

    decay_sweep = [
        #    1e3,
        #    10e3,
        # 20e3,
        # 35e3,
        # 50e3,
        # 70e3,
        # 100e3,
        # 150e3,
        200e3
    ]

    for k in range(1):
        for n in range(len(decay_sweep)):

            x_start = -1  # -1.4
            x_stop = 1
            x_step = 0.05

            y_start = -1
            y_stop = 1
            y_step = 0.05  # 0.085

            decay_time = decay_sweep[n]
            tomo_phase = tomo_phase_list[n]

            parameters = {
                "modes": [
                    "QUBIT",
                    "CAV",
                    "RR",
                ],
                "reps": 100,
                "wait_time": 2e6,  # 50e3,
                "fetch_period": 4,  # time between data fetching rounds in sec
                "delay": 80,  # 160,  # 100# wait time between opposite sign displacements
                "u1_amp_scale": coeffs[0],
                "v1_amp_scale": coeffs[1],
                "u2_amp_scale": coeffs[2],
                "v2_amp_scale": coeffs[3],
                "u3_amp_scale": coeffs[4],
                "v3_amp_scale": coeffs[5],
                "v_cat_amp_scale": v_cat_amp_scale,
                "decay_time": decay_time,
                "tomo_phase": tomo_phase,
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
                "cat_cav_ecd_displace": "constant_cos_ECD_3",
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
                "skip_plot": True,
            }

            experiment = sq_cat_decay_6db_oddcat(**parameters)
            experiment.setup_plot(**plot_parameters)

            prof.run(experiment)
