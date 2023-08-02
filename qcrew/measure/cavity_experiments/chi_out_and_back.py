"""
A python class describing a cavity T1 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class ChiOutAndBack(Experiment):

    name = "chi_out_and_back"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op1",
        "qubit_op2",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "tau",  # wait time
    }

    def __init__(
        self, cav_op, qubit_op1, qubit_op2, tau, fit_fn="gaussian", **other_params
    ):

        self.cav_op = cav_op
        self.qubit_op1 = qubit_op1
        self.qubit_op2 = qubit_op2
        self.tau = tau
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        cav.play(self.cav_op)  # play displacement to cavity
        qua.align(qubit.name, cav.name)  # align all modes
        qubit.play(self.qubit_op1)
        qua.align(qubit.name, cav.name)
        qua.wait(int(self.tau // 4), cav.name)  # wait rotation
        cav.play(self.cav_op, phase=self.x)  # 0.5 for minus sign and then sweep
        qua.align(qubit.name, cav.name)  # align all modes
        qubit.play(self.qubit_op2)
        qua.align(qubit.name, rr.name)  # align all modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # tream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 0
    x_stop = 2
    x_step = 0.01
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR"],
        "reps": 50000,
        "wait_time": 1.2e3,
        "tau": 1600,
        "x_sweep": ((x_start), (x_stop + x_step / 2), (x_step)),
        "qubit_op1": "pi",
        "qubit_op2": "pi_selective",
        "cav_op": "alice_large_displacement",
        "fetch_period": 4,
        "single_shot": False,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Cavity relaxation time (clock cycles)",
    }

    experiment = ChiOutAndBack(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
