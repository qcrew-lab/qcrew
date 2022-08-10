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


# ---------------------------------- Class -------------------------------------


class ECDDebug(Experiment):

    name = "ecd_debug"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op_ecd",  # fixed displacement.
        "cav_op_qfunc",  # displacement with varying amp to sweep phase space
        "qubit_op1_ecd",  # pi2 pulse
        "qubit_op2_ecd",  # pi pulse
        "qubit_op_qfunc",  # conditional pi pulse
        "ecd_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "fit_fn",  # fit function
        "delay",  # describe...
        "cav_op_d",
        "d_amp_scale",
    }

    def __init__(
        self,
        cav_op_qfunc,
        cav_op_ecd,
        cav_op_d,
        qubit_op_qfunc,
        qubit_op1_ecd,
        qubit_op2_ecd,
        ecd_amp_scale,
        d_amp_scale,
        fit_fn=None,
        delay=4,
        measure_real=True,
        **other_params
    ):
        self.cav_op_qfunc = cav_op_qfunc
        self.cav_op_ecd = cav_op_ecd
        self.cav_op_d = cav_op_d
        self.qubit_op_qfunc = qubit_op_qfunc
        self.qubit_op1_ecd = qubit_op1_ecd
        self.qubit_op2_ecd = qubit_op2_ecd
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real
        self.ecd_amp_scale = ecd_amp_scale
        self.d_amp_scale = d_amp_scale

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, cav_drive, rr_drive = self.modes  # get the modes

        # one iteration of the squeezing protcol
        qua.reset_frame(cav.name)

        if 1:
            # first U
            ## U = R_pi/2 - ECD - R_-pi/2
            # Initialize the qubit in a supersposition state

            # R_pi/2
            qubit.play(self.qubit_op1_ecd, phase=0)

            # ECD Gate
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd, ampx=self.ecd_amp_scale, phase=0
            )  # First positive displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd, ampx=-self.ecd_amp_scale, phase=0
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(
                self.qubit_op2_ecd, phase=0
            )  # pi pulse to flip the qubit state (echo)
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd, ampx=-self.ecd_amp_scale, phase=0
            )  # Second negative displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd, ampx=self.ecd_amp_scale, phase=0
            )  # Second positive displacement

            qua.align(qubit.name, cav.name)

            # R_-pi/2
            # qubit.play(self.qubit_op1_ecd, phase = 0.5)
            # qua.align(qubit.name, cav.name)

            # recentering displacement
            # cav.play(self.cav_op_ecd, ampx=-0.05, phase=0)
            # cav.play(self.cav_op_ecd, ampx=-0.3, phase=0.25)

        if 0:
            ## V = R_pi/2 - ECD - R_-pi/2 Second V

            # R_pi/2
            qubit.play(self.qubit_op1_ecd, phase=0.25)

            # ECD Gate
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd, ampx=self.ecd_amp_scale, phase=0.25
            )  # First positive displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd, ampx=-self.ecd_amp_scale, phase=0.25
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(
                self.qubit_op2_ecd, phase=0.25
            )  # pi pulse to flip the qubit state (echo)
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd, ampx=-self.ecd_amp_scale, phase=0.25
            )  # Second negative displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd, ampx=self.ecd_amp_scale, phase=0.25
            )  # Second positive displacement

            # R_-pi/2
            qubit.play(self.qubit_op1_ecd, phase=0.75)
            qua.align(qubit.name, cav.name)

            # recentering negative displacement
            cav.play(self.cav_op_ecd, ampx=-0.182, phase=0)
            cav.play(self.cav_op_ecd, ampx=0.1873, phase=0.25)

            qua.align(qubit.name, cav.name)

        # qua.wait(int(2000// 4), cav.name)

        # Measure the created state with the qfunc
        cav.play(self.cav_op_qfunc, ampx=self.x, phase=0)  # displacement in I direction
        cav.play(
            self.cav_op_qfunc, ampx=self.y, phase=0.25
        )  # displacement in Q direction
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_qfunc)  # play qubit selective pi-pulse
        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.align(cav.name, qubit.name, rr.name, cav_drive.name, rr_drive.name)
        # cav_drive.play("constant_cos", duration=200e3, ampx=1.6)
        # rr_drive.play("constant_cos", duration=200e3, ampx=1.4)
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    x_start = -1.6
    x_stop = 1.6
    x_step = 0.1

    y_start = -1.6
    y_stop = 1.6
    y_step = 0.1

    ecd_amp_scale = 1
    d_amp_scale = 0.5

    parameters = {
        "modes": ["QUBIT", "CAV", "RR", "CAV_DRIVE", "RR_DRIVE"],
        "reps": 500,
        "wait_time": 3e6,  # 50e3,
        "fetch_period": 8,  # time between data fetching rounds in sec
        "delay": 100,  # 100# wait time between opposite sign displacements
        "ecd_amp_scale": ecd_amp_scale,
        "d_amp_scale": d_amp_scale,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op1_ecd": "constant_cos_pi2",
        "qubit_op2_ecd": "constant_cos_pi",
        "qubit_op_qfunc": "pi_selective_1",
        "cav_op_ecd": "constant_cos_ECD",
        "cav_op_qfunc": "constant_cos_cohstate_1",
        "cav_op_d": "constant_cos_cohstate_1",
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
    }

    experiment = ECDDebug(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
