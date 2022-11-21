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


class ECDchar1D(Experiment):

    name = "ECD_char_1D"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "char_func_displacement",  # fixed displacement.
        "cav_ecd_displace",
        "cav_ecd_displace_special",
        "cat_cav_ecd_displace",
        "u1_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v1_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u2_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v2_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u3_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v3_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u_cat_amp_scale",
        "ecd_amp_scale",
        "qubit_pi2",  # operation used for exciting the qubit
        "qubit_pi",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(
        self,
        char_func_displacement,
        cav_ecd_displace,
        cav_ecd_displace_special,
        cat_cav_ecd_displace,
        u1_amp_scale,
        v1_amp_scale,
        u2_amp_scale,
        v2_amp_scale,
        u3_amp_scale,
        v3_amp_scale,
        ecd_amp_scale,
        u_cat_amp_scale,
        qubit_pi,
        qubit_pi2,
        delay,
        fit_fn="exponential_cosine_scale",  # fitting scale=2
        # fit_fn='gaussian',
        measure_real=True,
        **other_params
    ):

        self.char_func_displacement = char_func_displacement
        self.cav_ecd_displace = cav_ecd_displace
        self.cav_ecd_displace_special = cav_ecd_displace_special
        self.cat_cav_ecd_displace = cat_cav_ecd_displace
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
        self.ecd_amp_scale = ecd_amp_scale
        self.u_cat_amp_scale = u_cat_amp_scale

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.reset_phase(qubit.name)
        # state creation
        if 0:
            cav.play("constant_cos_cohstate_1", phase=0, ampx=1.5)
            qua.align()  # align measurement

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
            qubit.play(self.qubit_pi)
            qua.align()
            cav.play("constant_cos_cohstate_1", ampx=-0.02)

        # qua.update_frequency(qubit.name, int(49.8e6), keep_phase=True)
        # Measure 1D char func
        Char_1D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            ampx=0,
            delay=self.delay,
            measure_real=self.measure_real,
            tomo_phase=-0.05,
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

        # qua.update_frequency(qubit.name, int(50e6), keep_phase=True)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.7
    x_stop = 1.7
    x_step = 0.03

    u1_amp_scale = -0.845
    v1_amp_scale = 0.613

    u2_amp_scale = 1.319
    v2_amp_scale = 0.30

    u3_amp_scale = -0.91
    v3_amp_scale = -0.80
    ecd_amp_scale = 1  # 0.752
    u_cat_amp_scale = 1.2

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 400,
        "wait_time": 2.5e6,
        "fetch_period": 3,  # time between data fetching rounds in sec
        "delay": 80,  # pi/chi
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_pi2": "pi2",
        "qubit_pi": "pi",
        "char_func_displacement": "constant_cos_ECD_3",
        "cav_ecd_displace": "constant_cos_ECD_3",
        "cav_ecd_displace_special": "constant_cos_ECD_3",
        "cat_cav_ecd_displace": "constant_cos_ECD_3",
        "single_shot": False,
        "plot_quad": "I_AVG",
        "measure_real": True,
        "u1_amp_scale": u1_amp_scale,
        "v1_amp_scale": v1_amp_scale,
        "u2_amp_scale": u2_amp_scale,
        "v2_amp_scale": v2_amp_scale,
        "u3_amp_scale": u3_amp_scale,
        "v3_amp_scale": v3_amp_scale,
        "ecd_amp_scale": ecd_amp_scale,
        "u_cat_amp_scale": u_cat_amp_scale,
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
    }

    experiment = ECDchar1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
