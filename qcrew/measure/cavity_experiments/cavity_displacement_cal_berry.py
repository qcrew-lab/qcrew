"""
This script follows Fig S4 from Quantum error correction of a qubit encoded in grid states of an oscillator
A. Eickbusch et al.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import ECD


# ---------------------------------- Class -------------------------------------


class CavityDisplacementCalBerry(Experiment):

    name = "cavity_displacement_cal_berry"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_disp",
        "cav_disp_ecd",  # operation for displacing the cavity
        "qubit_pi2",
        "qubit_pi",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
        "measure_real",
        "ecd_amp_scale",
        "d_amp_scale",
    }

    def __init__(
        self,
        cav_disp,
        cav_disp_ecd,
        qubit_pi2,
        qubit_pi,
        ecd_amp_scale,
        d_amp_scale,
        fit_fn="sine",
        delay=4,
        measure_real=True,
        **other_params
    ):
        self.cav_disp = cav_disp
        self.cav_disp_ecd = cav_disp_ecd
        self.qubit_pi2 = qubit_pi2
        self.qubit_pi = qubit_pi
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

        if 1:  # sweep D(a)

            qua.reset_frame(cav.name)

            # Bring qubit into superpositon
            qubit.play(self.qubit_pi2)
            qua.align(qubit.name, cav.name)
            # first ECD
            ECD(
                cav,
                qubit,
                self.cav_disp_ecd,
                self.qubit_pi,
                ampx=self.ecd_amp_scale,
                phase=0,
                delay=self.delay,
            )

            # revert pi pulse in ecd gate
            qua.align(qubit.name, cav.name)
            qubit.play(self.qubit_pi, phase=0.75)

            # Do the first displacement D(beta)
            qua.align(qubit.name, cav.name)
            cav.play(self.cav_disp, ampx=self.x * self.d_amp_scale, phase=0.0)

            # second ECD with negativ amp
            ECD(
                cav,
                qubit,
                self.cav_disp_ecd,
                self.qubit_pi,
                ampx=-self.ecd_amp_scale,
                phase=0,
                delay=self.delay,
            )

            # revert pi pulse in ecd gate
            qua.align(qubit.name, cav.name)
            qubit.play(self.qubit_pi, phase=0.75)

            # Do the second displacement D(-beta)
            qua.align(qubit.name, cav.name)
            cav.play(self.cav_disp, ampx=-self.x * self.d_amp_scale, phase=0)

        if 0:  # sweep ECD(b) by sweepin its alphas

            qua.reset_frame(cav.name)

            # Bring qubit into superpositon
            qubit.play(self.qubit_pi2)

            # Do the first ECD gate
            ECD(
                cav,
                qubit,
                self.cav_disp_ecd,
                self.qubit_pi,
                ampx=self.x,
                phase=0,
                delay=self.delay,
            )
            # Second positive displacement
            # revert pi pulse in ecd gate

            qua.align(qubit.name, cav.name)
            qubit.play(self.qubit_pi)

            # Do the first displacement D(beta) sweep
            qua.align(qubit.name, cav.name)
            cav.play(self.cav_disp, ampx=1, phase=0.0)

            # Do the second ECD gate
            ECD(
                cav,
                qubit,
                self.cav_disp_ecd,
                self.qubit_pi,
                ampx=-self.x,
                phase=0,
                delay=self.delay,
            )

            # revert pi pulse in ecd gate
            qua.align(qubit.name, cav.name)
            qubit.play(self.qubit_pi)

            # Do the second displacement
            qua.align(qubit.name, cav.name)
            cav.play(self.cav_disp, ampx=-1, phase=0)

        # prepare sigmax measurement
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_pi2)

        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 0
    x_stop = 1.9
    x_step = 0.05

    ecd_amp_scale = 1
    d_amp_scale = 1

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 10000,
        "wait_time": 3e6,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 50,  # wait time between opposite sign displacements
        "ecd_amp_scale": ecd_amp_scale,
        "d_amp_scale": d_amp_scale,
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "qubit_pi2": "constant_cos_pi2",
        "qubit_pi": "constant_cos_pi",
        "cav_disp": "constant_cos_cohstate_1",
        "cav_disp_ecd": "constant_cos_ECD",
        # "ECD_phase": 0
        "measure_real": True,  # measure real part of char function if True, imag Part if false
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
    }

    experiment = CavityDisplacementCalBerry(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
