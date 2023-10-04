"""
A python class describing a T2 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from cmath import phase
from re import X
from typing import ClassVar

from betterproto import T

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import qcrew.measure.qua_macros as macros

import numpy as np

# ---------------------------------- Class -------------------------------------


class T2(Experiment):
    name = "T2"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "detuning",  # qubit pulse detuning
    }

    def __init__(
        self, qubit_op, rr_drive, drive_amp, ring_up,detuning=0, fit_fn="exp_decay_sine", **other_params
    ):
        self.qubit_op = qubit_op  # half pi pulse
        self.fit_fn = fit_fn
        self.detuning = detuning  # frequency detuning of qubit operation
        self.rr_drive = rr_drive
        self.drive_amp = drive_amp
        self.ring_up = ring_up

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """

        factor = qua.declare(qua.fixed)
        qua.assign(factor, self.detuning * 4 * 1e-9)

        qubit, rr = self.modes  # get the modes

        qua.reset_frame(qubit.name)
        rr.play(self.rr_drive, duration=(self.x + int(32) + int(self.ring_up)), ampx=self.drive_amp)
        qua.wait(int(self.ring_up))
        qubit.play(self.qubit_op)  # play half pi qubit pulse
        qua.wait(self.x, qubit.name)
        qua.assign(self.phase, qua.Cast.mul_fixed_by_int(factor, self.x))
        qubit.play(self.qubit_op, phase=self.phase)  # play half pi qubit pulse
        qua.align(qubit.name, rr.name)  # wait last qubit pulse to end
        qua.wait(int(320))
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 4
    x_stop = 60
    x_step = 1
    detuning_ = 16e6  # 1.12e6
    drive_amp = 1
    ring_up_time = 380 # clock cycle

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 1000,
        "wait_time": 500e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        # "y_sweep": [4, 38, 76, 152, 228, 304, 380, 475, 570, 665, 760],
        # "y_sweep": [9, 57, 114, 190, 266, 342, 428, 522, 618, 712],
        "qubit_op": "qubit_gaussian_short_pi2_pulse",
        "detuning": int(detuning_),
        "single_shot": True,
        "drive_amp": drive_amp,
        "rr_drive": "constant_drive",
        "ring_up":ring_up_time,
        "fetch_period": 2,
        # "fit_fn": "ramsey_photon_fit",
        "extra_vars": {
            "phase": macros.ExpVariable(
                var_type=qua.fixed,
                tag="phase",
                average=True,
                buffer=True,
                save_all=True,
            )
        },
        # "plot_quad": "I_AVG",
        # "fetch_period": 2,
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = T2(**parameters)
    experiment.name = ("T2_steadydrive_ampx0.1imes{}_".format(drive_amp))
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
