"""
A python class describing a cavity displacement calibration using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class CavityDisplacementCal(Experiment):

    name = "cavity_displacement_cal"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn="displacement_cal", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        cav.play(self.cav_op, ampx=self.x)  # play displacement to cavity
        qua.align(cav.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align all modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 0
    x_stop =  1.5
    x_step = 0.02
    
    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 10000,
        "wait_time": 1000000,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_op": "pi_selective",
        "cav_op": "gaussian_pulse",
    }

    plot_parameters = {
        "xlabel": "Cavity pulse amplitude scaling",
    }

    experiment = CavityDisplacementCal(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
