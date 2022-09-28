"""
This script will perform the necessary pulse scaling to convert between the real
pulse (with attenuation) to the pulse given by pygrape/qutip simulations
"""
from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Cavity_Pulse_Calibration(Experiment):

    name = "cavity_pulse_calibration"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = None

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
    '''
    Idea: We will read out the ".npz" file previously generated, and play the pulse multiplied by
    some amplitude scaling constant. We will sweep over this amplitude scaling constant, and find 
    the point where the pi-pulse actually becomes a pi-pulse.
    '''

    amp_start = 0
    amp_stop = 1.8
    amp_step = 0.1

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 10000,
        "wait_time": 1000000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "optimal_pi",
    }

    plot_parameters = {
        "xlabel": "Pulse Amplitude",
    }

    experiment = Cavity_Pulse_Calibration(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
