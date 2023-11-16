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
        "delay",  # describe...
        "fit_fn",  # fit function
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
        delay,
        fit_fn="sine", 
        **other_params
    ):
        self.cav_disp = cav_disp
        self.cav_disp_ecd = cav_disp_ecd
        self.qubit_pi2 = qubit_pi2
        self.qubit_pi = qubit_pi
        self.delay = delay
        self.fit_fn = fit_fn
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
                delay=self.delay,
                tomo_phase=0,
                qubit_phase = 0.25
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
                delay=self.delay,
                tomo_phase=0,
                qubit_phase = 0.25
            )

            # revert pi pulse in ecd gate
            qua.align(qubit.name, cav.name)
            qubit.play(self.qubit_pi, phase=0.75)

            # Do the second displacement D(-beta)
            qua.align(qubit.name, cav.name)
            cav.play(self.cav_disp, ampx=-self.x * self.d_amp_scale, phase=0)

        # prepare sigmax measurement
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_pi2)

        ## measurement
        qua.align(rr.name, "QUBIT_EF", qubit.name)
        # qua.wait(int(220 // 4), rr.name, "QUBIT_EF")
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 0.1
    x_stop = 1.9
    x_step = 0.03

    ecd_amp_scale = 1
    d_amp_scale = 1

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR"],
        "reps": 500,
        "wait_time": 1e6,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 160,  # wait time between opposite sign displacements
        "ecd_amp_scale": ecd_amp_scale,
        "d_amp_scale": d_amp_scale,
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "qubit_pi2": "gaussian_pi2_short_ecd",
        "qubit_pi": "gaussian_pi_short_ecd",
        "cav_disp": "cohstate_1_short",
        "cav_disp_ecd": "ecd2_displacement",
        # "ECD_phase": 0
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
    }

    experiment = CavityDisplacementCalBerry(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)