"""
A python class describing a cavity Q-switching experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Qswitching(Experiment):

    name = "Q_switching"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, drive1_op, drive2_op, fit_fn="cohstate_decay", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.drive1_op = drive1_op
        self.drive2_op = drive2_op

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        cav.play(self.cav_op, ampx = 1.8)  # play displacement to cavity
        qua.align(cav.name, qubit.name)  # align all modes
        cav.play(self.drive1_op, length = self.x, ampx = 1.8)  # play drive1 to cavity
        qua.update_frequency(rr.name, self.y)  # update resonator pulse frequency
        rr.play(self.drive2_op, ampx = 1.8)  # play drive2 to cavity
        qua.align(cav.name, rr.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align all modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 16
    x_stop = 100e3
    x_step = 1e3
    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 20000,
        "wait_time": 10e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        "qubit_op": "pi_selective3",
        "cav_op": "cohstate_1",
        "drive1_op": "constant_pulse",
        "cav_op": "cohstate_1",
        "drive2_op": "constant_pulse",
        "cav_op": "cohstate_1",
        
    }

    plot_parameters = {
        "xlabel": "Cavity relaxation time (clock cycles)",
    }

    experiment = Qswitching(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
