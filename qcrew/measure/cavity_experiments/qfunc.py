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


class QFunction(Experiment):

    name = "Qfunction"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn="gaussian", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, cav_drive, rr_drive = self.modes  # get the modes
        qua.reset_frame(cav.name)
        # cav.play(self.cav_op, phase=0)  # initial state creation
        qua.align(qubit.name, cav.name)  # align measurement
        # qubit.play("constant_cos_pi2")
        # qua.wait(int(16), cav.name, qubit.name)
        # qua.wait(int(360), cav.name, qubit.name)
        cav.play(self.cav_op, ampx=self.x, phase=0)  # displacement in I direction
        cav.play(self.cav_op, ampx=self.y, phase=0.25)  # displacement in Q direction
        qua.align(cav.name, qubit.name)
        # qubit.play("constant_cos_pi2")
        qubit.play(self.qubit_op)  # play qubit selective pi-pulse
        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.align(cav.name, qubit.name, rr.name, cav_drive.name, rr_drive.name)
        cav_drive.play("constant_cos", duration=200e3, ampx=1.6)
        rr_drive.play("constant_cos", duration=200e3, ampx=1.4)
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.5  # 1.5
    x_stop = 1.5
    x_step = 0.075

    y_start = -1.5
    y_stop = 1.5
    y_step = 0.075

    parameters = {
        "modes": ["QUBIT", "CAV", "RR", "CAV_DRIVE", "RR_DRIVE"],
        "reps": 500,
        "wait_time": 50e3,
        "fetch_period": 4,  # time between data fetching rounds in sec
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "pi_selective_1",
        "cav_op": "constant_cos_cohstate_1",
        "single_shot": True,
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "err": False,
        "cmap": "bwr",
    }

    experiment = QFunction(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
