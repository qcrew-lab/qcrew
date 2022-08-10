"""
A python class describing a cavity T1 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from email.policy import default
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

    def __init__(
        self, cav_op, qubit_op, fit_fn="cohstate_decay", **other_params
    ):  # "cohstate_decay",

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        # qubit, cav, rr = self.modes  # get the modes
        qubit, cav, rr, cav_drive2, rr_drive = self.modes

        cav.play(self.cav_op, ampx=1.4)  # play displacement to cavity
        qua.align(
            cav.name, qubit.name, rr.name, rr_drive.name, cav_drive2.name
        ) 
        # cav_drive2.play("gaussian_pulse", duration=self.x, ampx=1.4)
        # rr_drive.play("gaussian_pulse", duration=self.x, ampx=0.5)
        qua.wait(self.x, cav.name)  # wait relaxation
        qua.align(
            cav.name, qubit.name, rr.name, rr_drive.name, cav_drive2.name
        )  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(
            cav.name, qubit.name, rr.name, rr_drive.name, cav_drive2.name
        )  # align all modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset
        qua.align(
            cav.name, qubit.name, rr.name, rr_drive.name, cav_drive2.name
        )  # align all modes
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 4
    x_stop = 1500e3
    x_step = 20e3
    parameters = {
        # "modes": ["QUBIT", "CAV", "RR"],
        "modes": ["QUBIT", "CAV", "RR", "CAV_DRIVE2", "RR_DRIVE"],
        "reps": 5000,
        "wait_time": 5e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "pi_selective_1",
        "cav_op": "constant_cos_cohstate_1_test",
        "fetch_period": 15,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Cavity relaxation time (clock cycles)",
    }

    experiment = CavityT1(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
