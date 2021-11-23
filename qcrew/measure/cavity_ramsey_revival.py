"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class RamseyRevival(Experiment):

    name = "ramsey_revival"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op,  qubit_op, fit_fn="sine", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav,  rr = self.modes  # get the modes

        cav.play(self.cav_op, ampx=1) # create displacement in the cavity
        qua.align(cav.name, qubit.name) # wait for cav pulse to end
        qubit.play(self.qubit_op)  # bring qubit into superposition state
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qubit.play(self.qubit_op)  # return qubit into ground state if t = n*2pi/chi
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT","CAV", "RR"],
        "reps": 20000,
        "wait_time": 32000,
        "x_sweep": (int(16), int(1000 + 40 / 2), int(40)),
        "cav_op" : "constant_pulse",
        "qubit_op": "pi2",
    }

    plot_parameters = {
        "xlabel": "Wait time in clock cycles",
    }

    experiment = RamseyRevival(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
