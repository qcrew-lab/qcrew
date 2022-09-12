'''
This script will perform the necessary pulse scaling to convert between the real
pulse (with attenuation) to the pulse given by pygrape/qutip simulations
'''
from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Qubit_Pulse_Calibration(Experiment):

    name = "qubit_pulse_calibration"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, **other_params):

        self.qubit_op = qubit_op

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qubit.play(self.qubit_op, ampx = self.x)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------


if __name__ == "__main__":

    amp_start = 0
    amp_stop = 2
    amp_step = 0.1

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 50000,
        "wait_time": 1000000,
        "amp_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "numerical_pi", # This needs modification
    }

    plot_parameters = {
        "xlabel": "Pulse Amplitude",
    }

    experiment = Qubit_Pulse_Calibration(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)

