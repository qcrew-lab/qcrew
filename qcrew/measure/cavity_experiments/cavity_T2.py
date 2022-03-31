"""
A python class describing a cavity T2 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class CavityT2(Experiment):

    name = "cavity_T2"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn="exp_decay", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        # TODO work in progress

        # Prepare initial state (|0> + |1>)/sqrt(2)
        cav.play(self.cav_op, ampx=0.44 * 0.56)  # displace by beta = 0.56
        qua.align(cav.name, qubit.name)  # align pulses
        qubit.play(self.qubit_op)  # SNAP: play pi pulse around X
        qubit.play(self.qubit_op, phase=1.0)  # SNAP: play pi pulse around -X
        qua.align(cav.name, qubit.name)  # align pulses
        cav.play(self.cav_op, ampx=0.44 * -0.26)  # displace by beta = -0.26

        # Wait relaxation
        qua.wait(self.x, cav.name)

        # Measure cavity state
        qua.align(cav.name, qubit.name)  # align pulses
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 40
    x_stop = 100e3
    x_step = 1e3
    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 50000,
        "wait_time": 100000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "pi",
        "cav_op": "gaussian_pulse",
    }

    plot_parameters = {
        "xlabel": "Cavity relaxation time (clock cycles)",
    }

    experiment = CavityT2(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
