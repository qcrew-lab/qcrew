"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np


# ---------------------------------- Class -------------------------------------


class WignerFunction(Experiment):
    name = "wigner_function_rrdrive_steady"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(
        self,
        cav_op,
        qubit_op,
        rr_drive,
        drive_amp,
        qubitfre,
        fit_fn="gaussian",
        delay=4,
        **other_params
    ):
        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.delay = delay
        self.rr_drive = rr_drive
        self.drive_amp = drive_amp
        self.qubitfre = qubitfre

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)

        # cav.play(self.cav_op, ampx=0.0, phase=0.0)

        rr.play(
            self.rr_drive,
            duration=int(380 + 52 + 32 + self.delay // 4),
            ampx=self.drive_amp,
        )
        qua.wait(int(380))

        cav.play(self.cav_op, ampx=0, phase=0.25)  # displacement in I direction
        qua.update_frequency(qubit.name, self.qubitfre)
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(int(self.delay // 4), qubit.name)
        qubit.play(self.qubit_op, phase = self.y)  # play pi/2 pulse around X

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        qua.wait(int(320))
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        # rr.play("constant_pulse", duration=5e3, ampx=1)
        # cav.play("constant_pulse", duration=5e3, ampx=0.04)
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


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
        qubitfre = qubitfre_list[i]
        drive_amp = drive_amp_list[i]

        # x_start = -1.8
        # x_stop = 1.8
        # x_step = 0.2

        parameters = {
            "modes": ["QUBIT", "CAV", "RR"],
            "reps": 200,
            "wait_time": 16e6,
            "delay": 289,  # pi/chi
            "rr_drive": "constant_drive",
            # "x_sweep": (
            #     x_start,
            #     x_stop + x_step / 2,
            #     x_step,
            # ),  # ampitude sweep of the displacement pulses in the ECD
            "x_sweep": [-1, 1.5, 0.5],
            "y_sweep": [0, 0.5],
            "qubit_op": "qubit_gaussian_64ns_pi2_pulse",
            "drive_amp": drive_amp,
            "qubitfre": qubitfre,
            "cav_op": "coherent_1_long",
            "fit_fn": None,
            "single_shot": True,
            "fetch_period": 4,
            # "plot_quad": "I_AVG",
        }

        plot_parameters = {
            "xlabel": "X",
            "ylabel": "Y",
            "plot_type": "1D",
            "cmap": "bwr",
            "plot_err": None,
        }

        experiment = WignerFunction(**parameters)
        experiment.name = (
            "wigner_function_rrdrive_steady_No{}_ampx0.1times{}_QubitFre{}_".format(
                i, drive_amp, qubitfre / 1e6
            )
        )
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
