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


class ECDcharpostselect(Experiment):

    name = "ECD_char_postselect"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op_ecd",  # fixed displacement.
        "cav_op_ecd_2",
        "qubit_op1_ecd",  # pi2 pulse
        "qubit_op2_ecd",  # pi pulse
        "qubit_pi_selective",  # conditional pi pulse
        "ecd_amp_scale",  # amp scaling factor for cav_op_ecd pulse
        "ecd_amp_scale_2",
        "fit_fn",  # fit function
        "delay",  # describe...
        "cav_op_d",
        "d_amp_scale",
        "d_amp_scale_2"
    }

    def __init__(
        self,
        cav_op_ecd,
        cav_op_d,
        qubit_pi_selective,
        qubit_op1_ecd,
        qubit_op2_ecd,
        ecd_amp_scale,
        ecd_amp_scale_2,
        cav_op_ecd_2,
        d_amp_scale,
        d_amp_scale_2,
        fit_fn=None,
        delay=4,
        measure_real=True,
        **other_params
    ):
        self.cav_op_ecd = cav_op_ecd
        self.cav_op_ecd_2 = cav_op_ecd_2
        self.cav_op_d = cav_op_d
        self.qubit_pi_selective = qubit_pi_selective
        self.qubit_op1_ecd = qubit_op1_ecd
        self.qubit_op2_ecd = qubit_op2_ecd
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real
        self.ecd_amp_scale = ecd_amp_scale
        self.ecd_amp_scale_2 = ecd_amp_scale_2
        self.d_amp_scale = d_amp_scale
        self.d_amp_scale_2 = d_amp_scale_2
        self.internal_sweep = ["first", "second"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, cav_drive, rr_drive = self.modes  # get the modes

        qua.reset_frame(cav.name)

        if 0:
            qua.align()
            qubit.play(self.qubit_op1_ecd, phase=0)
            qua.align(cav.name, qubit.name)
            cav.play("constant_cos_cohstate_1", phase=0)
            # qua.align(cav.name, qubit.name)
            # qubit.play(self.qubit_op1_ecd, phase=0)
            # qua.wait(int(1200 // 4), cav.name, qubit.name)  # 5us
            qua.align()
            # qubit.play(self.qubit_op2_ecd, phase=0)

        ######################    ECD   ######################
        if 1:

            # U
            qubit.play(self.qubit_op1_ecd, phase=0.5)  # g+e

            qubit.play(self.qubit_op2_ecd, phase=0.75)  # pi

            # ECD Gate
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_2, ampx=self.ecd_amp_scale, phase=0
            )  # First positive displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_2, ampx=-self.ecd_amp_scale, phase=0
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(
                self.qubit_op2_ecd, phase=0.25
            )  # pi pulse to flip the qubit state (echo)
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_2, ampx=-self.ecd_amp_scale, phase=0
            )  # Second negative displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_2, ampx=self.ecd_amp_scale, phase=0
            )  # Second positive displacement

            qua.align(qubit.name, cav.name)

            qubit.play(self.qubit_op1_ecd, phase=0)  # U

            qua.align()  # wait for qubit pulse to end

        if 1:
            # V

            qubit.play(self.qubit_op1_ecd, phase=0.75)  # g+e

            # ECD Gate
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_2, ampx=self.d_amp_scale, phase=0.25
            )  # First positive displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_2, ampx=-self.d_amp_scale, phase=0.25
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(
                self.qubit_op2_ecd, phase=0.25
            )  # pi pulse to flip the qubit state (echo)
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_2, ampx=-self.d_amp_scale, phase=0.25
            )  # Second negative displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_2, ampx=self.d_amp_scale, phase=0.25
            )  # Second positive displacement

            qua.align(qubit.name, cav.name)

            qubit.play(
                self.qubit_op1_ecd, phase=0.75
            )  ## changed to test, to  be changed back

            qua.align()  # wait for qubit pulse to end

        if 1:

            # U
            qubit.play(self.qubit_op1_ecd, phase=0.5)  # g+e

            qubit.play(self.qubit_op2_ecd, phase=0.75)  # pi

            # ECD Gate
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_2, ampx=self.ecd_amp_scale_2, phase=0
            )  # First positive displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_2, ampx=-self.ecd_amp_scale_2, phase=0
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(
                self.qubit_op2_ecd, phase=0.25
            )  # pi pulse to flip the qubit state (echo)
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_2, ampx=-self.ecd_amp_scale_2, phase=0
            )  # Second negative displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_2, ampx=self.ecd_amp_scale_2, phase=0
            )  # Second positive displacement

            qua.align(qubit.name, cav.name)

            qubit.play(self.qubit_op1_ecd, phase=0)  # U

            qua.align()  # wait for qubit pulse to end
            
        if 1:
            # V

            qubit.play(self.qubit_op1_ecd, phase=0.75)  # g+e

            # ECD Gate
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_2, ampx=self.d_amp_scale_2, phase=0.25
            )  # First positive displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_2, ampx=-self.d_amp_scale_2, phase=0.25
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(
                self.qubit_op2_ecd, phase=0.25
            )  # pi pulse to flip the qubit state (echo)
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op_ecd_2, ampx=-self.d_amp_scale_2, phase=0.25
            )  # Second negative displacement
            qua.wait(
                int(self.delay // 4), cav.name, qubit.name
            )  # wait time between opposite sign displacements
            cav.play(
                self.cav_op_ecd_2, ampx=self.d_amp_scale_2, phase=0.25
            )  # Second positive displacement

            qua.align(qubit.name, cav.name)

            qubit.play(
                self.qubit_op1_ecd, phase=0.75
            )  ## changed to test, to  be changed back

            qua.align()  # wait for qubit pulse to end

        ###################### do a first measurement  #####################

        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        ######################  Measure the created state with charactristic function  #####################
        # bring qubit into superposition
        qua.align()
        qubit.play(self.qubit_op1_ecd)
        # start ECD gate
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(
            self.cav_op_ecd, ampx=self.x, phase=0.25
        )  # First positive displacement
        cav.play(self.cav_op_ecd, ampx=self.y, phase=0.5)

        qua.wait(int(self.delay // 4), cav.name)
        cav.play(self.cav_op_ecd, ampx=-self.x, phase=0.25)
        cav.play(self.cav_op_ecd, ampx=-self.y, phase=0.5)

        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_op2_ecd)  # play pi to flip qubit around X

        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play(
            self.cav_op_ecd, ampx=-self.x, phase=0.25
        )  # Second negative displacement
        cav.play(self.cav_op_ecd, ampx=-self.y, phase=0.5)

        qua.wait(int(self.delay // 4), cav.name)
        cav.play(
            self.cav_op_ecd, ampx=self.x, phase=0.25
        )  # Second positive displacement
        cav.play(self.cav_op_ecd, ampx=self.y, phase=0.5)

        qua.align(qubit.name, cav.name)

        qubit.play(
            self.qubit_op1_ecd, phase=0.0 if self.measure_real else 0.25
        )  # play pi/2 pulse around X or SY, to measure either the real or imaginary part of the characteristic function

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
    x_start = -1.7
    x_stop = 1.7
    x_step = 0.1

    y_start = -1.7
    y_stop = 1.7
    y_step = 0.1

    ecd_amp_scale = 0.969  #  the scale of constant_cos_ECD in ECD gate
    d_amp_scale = 0.22
    
    ecd_amp_scale_2 = -0.2864  #  the scale of constant_cos_ECD in ECD gate
    d_amp_scale_2 = -0.52

    parameters = {
        "modes": ["QUBIT", "CAV", "RR", "CAV_DRIVE", "RR_DRIVE"],
        "reps": 1000,
        "wait_time": 4e6,  # 50e3,
        "fetch_period": 4,  # time between data fetching rounds in sec
        "delay": 50,  # 160,  # 100# wait time between opposite sign displacements
        "ecd_amp_scale": ecd_amp_scale,
        "d_amp_scale": d_amp_scale,
        "ecd_amp_scale_2": ecd_amp_scale_2,
        "d_amp_scale_2": d_amp_scale_2,
        
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep":  (y_start, y_stop + y_step / 2, y_step),
        "qubit_op1_ecd": "constant_cos_pi2",
        "qubit_op2_ecd": "constant_cos_pi",
        "qubit_pi_selective": "pi_selective_1",
        "cav_op_ecd": "constant_cos_ECD",
        "cav_op_ecd_2": "constant_cos_ECD_2",
        "cav_op_d": "constant_cos_cohstate_1",
        "measure_real": True,
        # "plot_quad": "I_AVG",
        "single_shot": True,
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": False,
        "skip_plot": True,
    }

    experiment =ECDcharpostselect (**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
