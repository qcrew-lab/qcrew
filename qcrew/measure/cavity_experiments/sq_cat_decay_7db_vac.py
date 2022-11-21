"""
sq 7db vac
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class sq_cat_decay_7db_vac(Experiment):

    name = "sq_vcat_7db_vac"

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
        self.tomo_phase = tomo_phase
        self.decay_time = decay_time
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

        ###################### do a first measurement  #####################
        qua.align()
        rr.measure((self.I, self.Q))  # measure transmitted signal
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()  # align measurement
        qua.wait(int(80))

        ###################### decay the cat state  #####################

        # qua.wait(int(self.decay_time // 4))  ###### decay time

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
            tomo_phase=self.tomo_phase,  # -0.2
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

    sq7db_coeffs = [
        -0.83900019,
        0.56644014,
        1.2973754,
        -0.59798946,
        -1.26378237,
        0.38608659,
    ]
    coeffs = sq7db_coeffs
    v_cat_amp_scale = 0.53602  # 0.80403*2/3

    tomo_phase_list = [
        # -0.1559016 + 0.00135,
        # -0.27569139 + 0.00533 - 0.007479 + 0.00703,
        # -0.34568949 - 0.004 + 0.0037 +0.00183,
        # -0.18232261 - 0.03 + 0.005487 + 0.00379657,
        # -0.03664685 - 0.0304 + 0.00177 + 0.00502,
        # -0.16439758 - 0.0546 + 0.00243 + 0.0069992 + 0.00633,
        # -0.34623202 - 0.0925 + 0.00418 + 0.00233346 + 0.01248 + 0.043,
        # -0.18379108- 0.0925- 0.01841+ 0.00467813+ 0.00633+ 0.00225+ 0.31658- 0.07+ 0.00855+ 0.0019,
        # -0.00285389- 0.1486- 0.01622578+ 0.01009713+ 0.0150137+ 0.00839- 0.174- 0.1+ 0.25- 0.215+ 0.0713,
    ]

    decay_sweep = [1e3, 10e3, 20e3, 35e3, 50e3, 70e3, 100e3, 150e3, 200e3]
    # decay_sweep = [100e3]

    # for k in range(1):
    #     for n in range(len(decay_sweep)):

    # for n in range(len(decay_sweep)):
    for k in range(20):

        x_start = -1.9  # -1.7
        x_stop = 1.9
        x_step = 0.03

        y_start = -0.5  # -1.7
        y_stop = 0.5
        y_step = 0.03  # 0.085

        decay_time = 16  # decay_sweep[n]
        tomo_phase = 0.05 - 0.0017 -  0.0347 +0.0295  # tomo_phase_list[n]

        parameters = {
            "modes": [
                "QUBIT",
                "CAV",
                "RR",
            ],
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
            "v_cat_amp_scale": v_cat_amp_scale,
            "tomo_phase": tomo_phase,
            "decay_time": decay_time,
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

        experiment = sq_cat_decay_7db_vac(**parameters)
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
