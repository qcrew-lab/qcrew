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

from qcrew.measure.qua_macros import ECD, Char_2D, U, V


# ---------------------------------- Class -------------------------------------



class ECDchar(Experiment):

    name = "ECD_char"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "char_func_displacement",  # fixed displacement.
        "cav_ecd_displace",
        "qubit_pi",  # pi pulse
        "qubit_pi2",  # pi/2
        "u_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "v_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "fit_fn",  # fit function
        "delay",  # describe...
        "cav_displace_1",
        # "d_amp_scale",
    }

    def __init__(
        self,
        char_func_displacement,
        cav_displace_1,
        qubit_pi,
        qubit_pi2,
        u_amp_scale,
        v_amp_scale,
        cav_ecd_displace,
        # d_amp_scale,
        fit_fn=None,
        delay=4,
        measure_real=True,
        **other_params
    ):
        self.char_func_displacement = char_func_displacement
        self.cav_ecd_displace = cav_ecd_displace
        self.cav_displace_1 = cav_displace_1
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real
        self.u_amp_scale = u_amp_scale
        self.v_amp_scale = v_amp_scale
        # self.d_amp_scale = d_amp_scale
        # self.internal_sweep = ["first", "second"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, rr_drive = self.modes  # get the modes

        qua.reset_frame(cav.name, qubit.name)
        #cav.play('constant_cos_cohstate_1', amp = 1, phase = 0)
        #qua.align()  # align measurement
        
        if 1:
            qubit.play("oct_pulse")
            cav.play("oct_pulse")
            # cav.play("constant_cos_cohstate_1_long")
            qua.align()

        ######################  Measure the created state with charactristic function  #####################
        Char_2D(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            ampx_x=self.x,
            ampx_y=self.y,
            phase_x=0.25,  # 0.25,
            phase_y=0.5,  # 0.5,
            delay=self.delay,
            measure_real=self.measure_real,
        )

        # Measure cavity state
        qua.align()  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    x_start = -1.3
    x_stop = 1.3
    x_step = 0.1

    y_start = -1.3
    y_stop = 1.3
    y_step = 0.1

    u_amp_scale = 1  #  the scale of constant_cos_ECD in ECD gate
    v_amp_scale = -0.6

    parameters = {
        "modes": ["QUBIT", "CAV", "RR", "RR_DRIVE"],
        "reps": 500,
        "wait_time": 4e6,  # 50e3,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 50,  # 50,  # wait time between opposite sign displacements
        "u_amp_scale": u_amp_scale,
        "v_amp_scale": v_amp_scale,
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_pi": "constant_cos_pi",
        "qubit_pi2": "constant_cos_pi2",
        "char_func_displacement": "constant_cos_ECD_2",
        "cav_ecd_displace": "constant_cos_ECD_2",
        "cav_displace_1": "constant_cos_cohstate_2",
        "measure_real": True,
        "plot_quad": "I_AVG",
        # "single_shot": True,
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": False,
        # "skip_plot": False,
    }

    experiment = ECDchar(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
