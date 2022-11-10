"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class PowerRabi(Experiment):

    name = "power_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="sine", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, cav = self.modes  # get the modes

        # cav.play("cohstate1")
        # qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        # qua.align(cav.name, qubit.name)
        # cav.play("cohstate1", ampx=self.x)
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.play("constant_pulse", ampx=1)
        rr.play("constant_pulse", ampx=1)
        rr.play("constant_pulse", ampx=1)
        rr.play("constant_pulse", ampx=1)
        rr.play("constant_pulse", ampx=1)
        rr.play("constant_pulse", ampx=-1)
        rr.play("constant_pulse", ampx=-1)
        rr.play("constant_pulse", ampx=-1)
        rr.play("constant_pulse", ampx=-1)
        rr.play("constant_pulse", ampx=-1)

        # rr.mea
        # sure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1.8
    amp_stop = 1.8
    amp_step = 0.05

    parameters = {
        "modes": ["QUBIT", "RR", "CAV_Alice"],
        "reps": 100000,
        "wait_time": 150000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "constant_pulse",  # "gaussian_pi_selective_pulse3",
        # "single_shot": True,
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        # "zlimits": (0.35, 0.5)
    }

    experiment = PowerRabi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
