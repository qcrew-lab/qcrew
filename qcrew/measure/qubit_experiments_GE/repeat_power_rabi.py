"""
A python class describing a power rabi measurement with repeated qubit pulses using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua 

# ---------------------------------- Class -------------------------------------


class RepPowerRabi(Experiment):

    name = "repeat_power_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "pulse_number",  # number of times qubit pulse is repeated
    }

    def __init__(self, qubit_op, pulse_number, fit_fn="sine", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.pulse_number = pulse_number

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        for k in range(self.pulse_number):  # play qubit pulse multiple times
            qubit.play(self.qubit_op, ampx=self.x)
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    
    amp_start = -1.5
    amp_stop = 1.5
    amp_step = 0.05


    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 10000,
        "wait_time": 400000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "pi2",
        "pulse_number": 2,
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
    }

    experiment = RepPowerRabi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
