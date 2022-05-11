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

    def __init__(self, cav_op, qubit_op, fit_fn=None, **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the mode
        qua.reset_frame(qubit.name, cav.name)

        #cav.play("CD_cali", ampx=1, phase=0)

        qubit.play("pi_test")
        qua.align(qubit.name, cav.name)


        ############## first ECD gate##############
        cav.play("CD_cali", ampx=1, phase=0)  # First positive displacement
        qua.wait(
            int(160 // 4),
            cav.name,
            qubit.name,
        )  # wait time between opposite sign displacements
        cav.play("CD_cali", ampx=-1, phase=0)  # First negative displacement
        qua.align(qubit.name, cav.name)
        qubit.play("pi_test")  # pi pulse to flip the qubit state (echo)
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play("CD_cali", ampx=-1, phase=0)  # Second negative displacement
        qua.wait(
            int(160 // 4), cav.name, qubit.name
        )  # wait time between opposite sign displacements
        cav.play("CD_cali", ampx=1, phase=0)  # Second positive displacement
        qua.align(qubit.name, cav.name)

        ############## unconditional disp ##############
        cav.play("cohstate_1_test", ampx=1, phase=0)
        qua.align(qubit.name, cav.name)

        ############## reset to initial qubit state ##############
        qubit.play("pi_test")
        qua.align(qubit.name, cav.name)

        ############## second ECD gate##############
        cav.play("CD_cali", ampx=-1, phase=0)  # First positive displacement
        qua.wait(
            int(160 // 4),
            cav.name,
            qubit.name,
        )  # wait time between opposite sign displacements
        cav.play("CD_cali", ampx=1, phase=0)  # First negative displacement
        qua.align(qubit.name, cav.name)
        qubit.play("pi_test")  # pi pulse to flip the qubit state (echo)
        qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
        cav.play("CD_cali", ampx=1, phase=0)  # Second negative displacement
        qua.wait(
            int(160 // 4), cav.name, qubit.name
        )  # wait time between opposite sign displacements
        cav.play("CD_cali", ampx=-1, phase=0)  # Second positive displacement
        qua.align(qubit.name, cav.name)

        ############## unconditional disp ##############
        cav.play("cohstate_1_test", ampx=-1, phase=0)
        qua.align(qubit.name, cav.name)

        ############ measurement ################
        # qubit.play("pi_test")
        # qua.align(qubit.name, cav.name)
        cav.play(self.cav_op, ampx=-self.x, phase=0)  # displacement in I direction
        cav.play(self.cav_op, ampx=-self.y, phase=0.25)  # displacement in Q direction
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op)  # play qubit selective pi-pulse
        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name, rr.name, qubit.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.5
    x_stop = 1.5
    x_step = 0.1

    y_start = -1.5
    y_stop = 1.5
    y_step = 0.1

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 800,
        "wait_time": 160000,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "pi_selective",
        "cav_op": "cohstate_1",
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
