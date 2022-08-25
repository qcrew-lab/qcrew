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


class ECDcharacteristicfunc(Experiment):

    name = "ECD_characteristic_func"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op_ecd",  # fixed displacement.
        "qubit_op1_ecd",  # pi2 pulse
        "qubit_op2_ecd",  # pi pulse
        "qubit_pi_selective",  # conditional pi pulse
        "ecd_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "fit_fn",  # fit function
        "delay",  # describe...
        "cav_op_d",
        "d_amp_scale",
    }

    def __init__(
        self,
        cav_op_ecd,
        cav_op_d,
        qubit_pi_selective,
        qubit_op1_ecd,
        qubit_op2_ecd,
        ecd_amp_scale,
        cav_op_ecd_test,
        d_amp_scale,
        fit_fn=None,
        delay=4,
        measure_real=True,
        **other_params
    ):
        self.cav_op_ecd = cav_op_ecd
        self.cav_op_ecd_test = cav_op_ecd_test
        self.cav_op_d = cav_op_d
        self.qubit_pi_selective = qubit_pi_selective
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
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)

        if 1:
            qubit.play("oct_pulse_qubit")
            cav.play("oct_pulse_cavity")
            qua.align()

        ######################    pi/ - ECD - pi ######################
        if 0:
            #  cav.play(self.cav_op_ecd, ampx=1, phase=0)
            #  cav.play(self.cav_op_ecd, ampx=-1, phase=0)

            # e state
            # qubit.play(self.qubit_op2_ecd, phase=0)

            # ECD Gate
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_test, ampx=1, phase=0
            )  # First positive displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_test, ampx=-1, phase=0
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(
                self.qubit_op2_ecd, phase=0
            )  # pi pulse to flip the qubit state (echo)
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_test, ampx=-1, phase=0
            )  # Second negative displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_test, ampx=1, phase=0
            )  # Second positive displacement

            qua.align(qubit.name, cav.name)

            #  flip qubit to reverse first ecd
            # qubit.play(self.qubit_op2_ecd, phase=0)
            qubit.play(self.qubit_op2_ecd, phase=0)

            ###
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_test, ampx=-1, phase=0
            )  # First positive displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_test, ampx=1, phase=0
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(
                self.qubit_op2_ecd, phase=0
            )  # pi pulse to flip the qubit state (echo)
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_test, ampx=1, phase=0
            )  # Second negative displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_test, ampx=-1, phase=0
            )  # Second positive displacement
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            qubit.play(
                self.qubit_op2_ecd, phase=0)
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end

        ######################  Measure the created state with charactristic function  #####################

        # bring qubit into superposition
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op1_ecd)
        # start ECD gate
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(self.cav_op_ecd, ampx=self.x, phase=0.0)  # First positive displacement
        cav.play(self.cav_op_ecd, ampx=self.y, phase=0.25)

        qua.wait(int(self.delay // 4), cav.name)
        cav.play(
            self.cav_op_ecd, ampx=-self.x, phase=0.0
        )  # First negative displacement
        cav.play(self.cav_op_ecd, ampx=-self.y, phase=0.25)

        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_op2_ecd)  # play pi to flip qubit around X

        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(
            self.cav_op_ecd, ampx=-self.x, phase=0.0
        )  # Second negative displacement
        cav.play(self.cav_op_ecd, ampx=-self.y, phase=0.25)

        qua.wait(int(self.delay // 4), cav.name)
        cav.play(
            self.cav_op_ecd, ampx=self.x, phase=0.0
        )  # Second positive displacement
        cav.play(self.cav_op_ecd, ampx=self.y, phase=0.25)

        qua.align(qubit.name, cav.name)

        qubit.play(
            self.qubit_op1_ecd, phase=0.0 if self.measure_real else 0.25
        )  # play pi/2 pulse around X or SY, to measure either the real or imaginary part of the characteristic function

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    x_start = -1
    x_stop = 1
    x_step = 0.1

    y_start = -1
    y_stop = 1
    y_step = 0.1

    ecd_amp_scale = 1  #  the scale of constant_cos_ECD in ECD gate
    d_amp_scale = 1

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 100,
        "wait_time": 2.5e6,  # 50e3,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 50,  # 160,  # 100# wait time between opposite sign displacements
        "ecd_amp_scale": ecd_amp_scale,
        "d_amp_scale": d_amp_scale,
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op1_ecd": "constant_cos_pi2",
        "qubit_op2_ecd": "oct_pulse_qubit",
        "qubit_pi_selective": "pi_selective_1",
        "cav_op_ecd": "constant_cos_ECD_2",
        "cav_op_ecd_test": "oct_pulse_cavity",
        "cav_op_d": "constant_cos_cohstate_1",
        "measure_real": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": False,
    }

    experiment = ECDcharacteristicfunc(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
