"""
normal vac 1d
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class normal_vac_1d(Experiment):

    name = "normal_vac_1d"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "char_func_displacement",  # fixed displacement.
        "cav_ecd_displace",
        "cav_ecd_displace_special",
        "cat_cav_ecd_displace",
        "qubit_pi",  # pi pulse
        "qubit_pi2",  # pi/2
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
        Char_1D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            self.x,
            # self.y,
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

    for k in range(3):

        x_start = -1.9  # -1.7
        x_stop = 1.9
        x_step = 0.01

        # y_start = -1.5  # -1.7
        # y_stop = 1.5
        # y_step = 0.01  # 0.085

        decay_time = 16  # decay_sweep[n]
        tomo_phase = 0  # tomo_phase_list[n]

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
            "tomo_phase": tomo_phase,
            "decay_time": decay_time,
            "x_sweep": (
                x_start,
                x_stop + x_step / 2,
                x_step,
            ),  # ampitude sweep of the displacement pulses in the ECD
            # "y_sweep": (y_start, y_stop + y_step / 2, y_step),
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

        experiment = normal_vac_1d(**parameters)
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
