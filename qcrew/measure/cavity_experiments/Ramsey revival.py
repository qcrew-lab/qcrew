"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Ramseyrevival(Experiment):

    name = "Ramsey_revival"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, cav_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        #cav.play(self.cav_op, ampx=1)  # prepare cavity state
        qua.align(cav.name, qubit.name)  # align modes 
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.wait(self.x, qubit.name)
        qubit.play(self.qubit_op)  # play  qubit pulse with pi/2
        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 4
    x_stop = 1800
    x_step = 20

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 4000,
        "wait_time": 1200000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "constant_cos_pi2",
        "cav_op": "constant_cos_cohstate_1",
    }

    plot_parameters = {
        "xlabel": "Wait time (clock)",
    }

    experiment = Ramseyrevival(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
