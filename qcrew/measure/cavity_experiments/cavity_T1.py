"""
A python class describing a cavity T1 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class CavityT1(Experiment):

    name = "cavity_T1"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn="cohstate_decay", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = None

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        cav.play(self.cav_op)  # play displacement to cavity
        qua.wait(self.x, cav.name)  # wait relaxation
        qua.align(cav.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align all modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 100
    x_stop = 400e3
    x_step = 4e3
    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 40000,
        "wait_time": 3000000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "gaussian_pi_selective_pulse3",
        "cav_op": "cohstate1",
        "plot_quad": "Z_AVG",
        "fetch_period": 1.2,
        
    }

    plot_parameters = {
        "xlabel": "Cavity relaxation time (clock cycles)",
        "plot_err": None
    }

    experiment = CavityT1(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
