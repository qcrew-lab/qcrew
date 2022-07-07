"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import qcrew.measure.qua_macros as macros
import numpy as np


# ---------------------------------- Class -------------------------------------


class QFunction(Experiment):

    name = "Qfunction"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, cav_op, qubit_op, ddrop_params=None, fit_fn="gaussian", **other_params
    ):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.ddrop_params = ddrop_params

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (
            qubit,
            cav,
            rr,
            qubit_ef,
            cav_drive,
            rr_drive,
        ) = self.modes  # get the modes
        # cav_drive,
        if self.ddrop_params:
            macros.DDROP_reset(qubit, rr, **self.ddrop_params)
            # Use qubit_ef if also resetting F state
            # macros.DDROP_reset(qubit, rr, **self.ddrop_params, qubit_ef=qubit_ef)

        qua.reset_frame(cav.name)
        qua.align()
        # cav.play(self.cav_op, phase=0)  # initial state creation
        qua.align(qubit.name, cav.name)  # align measurement
        cav.play(self.cav_op, ampx=self.x, phase=0)  # displacement in I direction
        cav.play(self.cav_op, ampx=self.y, phase=0.25)  # displacement in Q direction
        qua.align(cav.name, qubit.name)

        qubit.play(self.qubit_op)  # play qubit selective pi-pulse
        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # qua.align()
        # wait system reset
        # cav_drive.play("constant_cos", duration=200e3, ampx=1.6)
        # rr_drive.play("constant_cos", duration=200e3, ampx=1.4)
        qua.wait(int(self.wait_time // 4))

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.5  # 1.5
    x_stop = 1.5
    x_step = 0.1

    y_start = -1.5
    y_stop = 1.5
    y_step = 0.1

    parameters = {
        "modes": [
            "QUBIT",
            "CAV",
            "RR",
            "QUBIT_EF",
            "CAV_DRIVE",
            "RR_DRIVE",
        ],
        "reps": 500,
        "wait_time": 3e6,
        "fetch_period": 10,  # time between data fetching rounds in sec
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "pi_selective_1",
        "cav_op": "constant_cos_ECD_test",
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "err": False,
        "cmap": "bwr",
    }

    ddrop_params = {
        "rr_ddrop_freq": int(-50.4e6),  # RR IF when playing the RR DDROP pulse
        "rr_steady_wait": 2000,  # in nanoseconds
        "ddrop_pulse": "ddrop_pulse",  # name of all ddrop pulses
    }
    experiment = QFunction(ddrop_params=None, **parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
