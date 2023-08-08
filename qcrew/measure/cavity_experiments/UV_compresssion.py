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


class UV_squeezing_optimise_char_1D(Experiment):

    name = "UV_squeezing_optimise_char_1D.py"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "char_func_displacement",  # fixed displacement.
        "cav_ecd_displace",
        "cav_ecd_displace_special",
        "u1_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v1_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u2_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v2_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "u3_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v3_amp_scale",  # amp scaling factor for cav_op_ecd pulse
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
        u1_amp_scale,
        v1_amp_scale,
        u2_amp_scale,
        v2_amp_scale,
        u3_amp_scale,
        v3_amp_scale,
        ecd_amp_scale,
        qubit_pi,
        qubit_pi2,
        delay,

        fit_fn='gaussian',
        measure_real=True,
        **other_params,
    ):

        self.char_func_displacement = char_func_displacement
        self.cav_ecd_displace = cav_ecd_displace
        self.cav_ecd_displace_special = cav_ecd_displace_special
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.delay = delay
        self.measure_real = measure_real
        self.u1_amp_scale = u1_amp_scale
        self.v1_amp_scale = v1_amp_scale
        self.u2_amp_scale = u2_amp_scale
        self.v2_amp_scale = v2_amp_scale
        self.u3_amp_scale = u3_amp_scale
        self.v3_amp_scale = v3_amp_scale
        self.ecd_amp_scale = ecd_amp_scale
        self.fit_fn = fit_fn


        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.reset_phase(qubit.name)

        # state creation

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

        if 0:
            U(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.u2_amp_scale,
                delay=self.delay,
            )
        if 0:
            V(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.v2_amp_scale,
                delay=self.delay,
            )
        if 0:
            U(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.u3_amp_scale,
                delay=self.delay,
            )
        if 0:
            V(
                cav,
                qubit,
                self.cav_ecd_displace,
                self.qubit_pi,
                self.qubit_pi2,
                ampx=self.v3_amp_scale,
                delay=self.delay,
            )
        # qua.align()
        # qua.update_frequency(qubit.name, int(49.8e6), keep_phase=True)
        # Measure 1D char func
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
    x_step = 0.05
    y_start = -1.7
    y_stop = 1.7
    y_step = 0.1


    sq3db_1_step = [
        1,
        -0.6,
        0,
        0,
        0,
        0,
    ]
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

    ecd_amp_scale = 1  # 0.752
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR"],
        "reps": 400,
        "wait_time": 200e3,
        "fetch_period": 3,  # time between data fetching rounds in sec
        "delay": 100,  # pi/chi
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_pi2": "pi2",
        "qubit_pi": "pi",
        "char_func_displacement": "daddy_ecd_2",
        "cav_ecd_displace": "daddy_ecd_1",
        "cav_ecd_displace_special": "daddy_ecd_2",
        "single_shot": False,
        "plot_quad": "I_AVG",
        "measure_real": True,
        "u1_amp_scale": coeffs[0],
        "v1_amp_scale": coeffs[1],
        "u2_amp_scale": coeffs[2],
        "v2_amp_scale": coeffs[3],
        "u3_amp_scale": coeffs[4],
        "v3_amp_scale": coeffs[5],
        "ecd_amp_scale": ecd_amp_scale,
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
    }

    experiment = UV_squeezing_optimise_char_1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
