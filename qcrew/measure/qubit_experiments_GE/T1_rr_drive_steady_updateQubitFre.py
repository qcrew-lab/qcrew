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
        self,
        qubit_op,
        rr_drive,
        drive_amp,
        qubitfre,
        ring_up,
        detuning=0,
        fit_fn="exp_decay_sine",
        **other_params
    ):
        self.qubit_op = qubit_op  # half pi pulse
        self.fit_fn = fit_fn
        self.detuning = detuning  # frequency detuning of qubit operation
        self.rr_drive = rr_drive
        self.drive_amp = drive_amp
        self.qubitfre = qubitfre
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
        qua.update_frequency(qubit.name, self.qubitfre)
        rr.play(
            self.rr_drive,
            duration=(self.x + int(30) + int(self.ring_up)),
            ampx=self.drive_amp,
        )
        qua.wait(int(self.ring_up))
        
        qubit.play(self.qubit_op)  # play pi qubit pulse
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    drive_amp_list = [
        0.0,
        0.0125,
        0.025,
        0.0375,
        0.05,
        0.0625,
        0.075,
        0.0875,
        0.1,
        0.1125,
        0.125,
        0.15,
        0.2,
        0.25,
        0.3,
        0.35,
        0.4,
        0.45,
        0.5,
        0.55,
        0.6,
        0.65,
        0.7,
        0.75,
        0.8,
    ]
    qubitfre_list = (
        np.array(
            [
                -60.0,
                -60.0,
                -60.0,
                -59.95,
                -60.0,
                -59.95,
                -60.1,
                -60.05,
                -60.1,
                -60.1,
                -60.0,
                -60.05,
                -60.15,
                -60.1,
                -60.25,
                -60.55,
                -60.65,
                -60.8,
                -61.1,
                -61.3,
                -61.75,
                -61.5,
                -62.1,
                -62.3,
                -63.0,
            ]
        )
        * 1e6
    )

    for i in range(len(drive_amp_list)):
        
        # i = 24
        x_start = 4
        x_stop = 190_000
        x_step = 4000

        drive_amp = drive_amp_list[i]
        qubitfre = qubitfre_list[i]
        ring_up_time = 380  # clock cycle

        parameters = {
            "modes": ["QUBIT", "RR"],
            "reps": 1000,
            "wait_time": 600e3,
            "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
            # "y_sweep": [4, 38, 76, 152, 228, 304, 380, 475, 570, 665, 760],
            # "y_sweep": [9, 57, 114, 190, 266, 342, 428, 522, 618, 712],
            "qubit_op": "qubit_gaussian_120ns_pi_pulse",
            # "detuning": int(detuning_),
            "single_shot": True,
            "drive_amp": drive_amp,
            "qubitfre": qubitfre,
            "rr_drive": "constant_drive",
            "ring_up": ring_up_time,
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
            "fetch_period": 2,
        }

        plot_parameters = {
            "xlabel": "Relaxation time (clock cycles)",
            "plot_err": None,
        }

        experiment = T2(**parameters)
        experiment.name = "T1_steadydrive_No{}_ampx0.1imes{}_QubitFre{}_".format(
            i, drive_amp, qubitfre / 1e6
        )
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
