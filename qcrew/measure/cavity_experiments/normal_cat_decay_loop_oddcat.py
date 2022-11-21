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


class normal_cat_decay_loop_oddcat(Experiment):

    name = "normal_cat_imag_with_pi2_phase"

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
        "u_cat_amp_scale",
        "fit_fn",  # fit function
        "delay",  # describe...
        "cav_displace_1",
        "ecd_amp_scale",
        "decay_time",
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
        cat_cav_ecd_displace,
        ecd_amp_scale,
        decay_time,
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
        self.u_cat_amp_scale = u_cat_amp_scale
        self.ecd_amp_scale = ecd_amp_scale
        self.decay_time = decay_time
        self.internal_sweep = ["first", "second", "third"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name, qubit.name)
        # qua.reset_phase(qubit.name)

        if 1:
            rr.measure((self.I, self.Q))  # measure transmitted signal
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()  # align measurement
            qua.wait(int(20))
            qua.align()

        if 1:
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
            qua.align()
            qubit.play(self.qubit_pi)  # remove this if creating even cat
            qua.align()
            cav.play("constant_cos_cohstate_1", ampx=-0.065)

        ###################### do a first measurement  #####################
        qua.align()
        rr.measure((self.I, self.Q))  # measure transmitted signal
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()  # align measurement
        qua.wait(int(20))
        qua.align()
        ###################### decay the cat state  #####################

        qua.wait(int(self.decay_time // 4))  ###### decay time
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
            tomo_phase=-0.215,
        )

        # Measure 1D char func
        # Char_1D_singledisplacement(
        #     cav,
        #     qubit,
        #     self.char_func_displacement,
        #     self.qubit_pi,
        #     self.qubit_pi2,
        #     ampx=self.x,
        #     delay=self.delay,
        #     measure_real=self.measure_real,
        #     tomo_phase=-0.215+0.25,
        # )

        # Measure cavity state
        qua.align()  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        # qua.update_frequency(qubit.name, 50e6)  # update resonator pulse frequency
        qua.wait(int(self.wait_time // 4))
        # qua.update_frequency(qubit.name, int(50e6), keep_phase=True)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":

    # decay_sweep = [1e3, 10e3, 20e3, 35e3, 50e3, 70e3, 100e3, 150e3, 200e3] #[16]  #
    ntimes = 5

    # decay_sweep = [1000, 10000, 16000, 30000, 50000, 70000, 100000, 150000, 200000]

    for k in range(ntimes):
        # for n in range(len(decay_sweep)):
        x_start = -1.7  # -1.4
        x_stop = 1.7
        x_step = 0.17  # 0.05

        y_start = -1.7
        y_stop = 1.7
        y_step = 0.17  # 0.05

        #### one UV (1, -0.6)
        #### two UV   (1.938, 0.44), (-0.572, -1.06)
        #### three UV (-0.845,  0.613),  (2.6368,  0.30), (-0.91, -0.80)

        u1_amp_scale = -0.845
        v1_amp_scale = 0.613

        u2_amp_scale = 1.319
        v2_amp_scale = 0.30

        u3_amp_scale = -0.91
        v3_amp_scale = -0.80

        u_cat_amp_scale = 1.2

        ecd_amp_scale = 1

        decay_time = 16

        parameters = {
            "modes": ["QUBIT", "CAV", "RR"],
            "reps": 100,
            "wait_time": 2e6,  # 50e3,
            "fetch_period": 4,  # time between data fetching rounds in sec
            "delay": 80,  # 160,  # 100# wait time between opposite sign displacements
            "u1_amp_scale": u1_amp_scale,
            "v1_amp_scale": v1_amp_scale,
            "u2_amp_scale": u2_amp_scale,
            "v2_amp_scale": v2_amp_scale,
            "u3_amp_scale": u3_amp_scale,
            "v3_amp_scale": v3_amp_scale,
            "ecd_amp_scale": ecd_amp_scale,
            "u_cat_amp_scale": u_cat_amp_scale,
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
            "measure_real": False,
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

        experiment = normal_cat_decay_loop_oddcat(**parameters)
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
