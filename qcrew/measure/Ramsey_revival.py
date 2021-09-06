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


class Ramseyrevival(Experiment):

    name = "Ramsey_revival"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn="sine", detuning=None, cav_amp = None, **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.detuning = detuning
        self.cav_amp = cav_amp

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        # TODO work in progress
        cav.play(self.cav_op, ampx = self.cav_amp)
        qua.align(cav.name, qubit.name)
        #qua.update_frequency(qubit.name, qubit.int_freq + self.detuning)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(self.x , qubit.name)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        #"modes": ["QUBIT", "RR"],
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 80000,
        "wait_time": 600000,
        "fetch_period": 3,  # time between data fetching rounds in sec
        "x_sweep": (int(16), int(2500 + 50 / 2), int(50)),
        "qubit_op": "pi2",
        "cav_op": "constant_pulse",
        "cav_amp": 0.182 * 2,
        "detuning": int(0),
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
        "plot_type": "1D",
        "err": True,
    }

    experiment = Ramseyrevival(**parameters)
    experiment.setup_plot(**plot_parameters)
    print(experiment.modes)
    prof.run(experiment)
