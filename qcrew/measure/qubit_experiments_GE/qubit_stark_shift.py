"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from pyexpat.model import XML_CTYPE_SEQ
from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class StarkShift(Experiment):

    name = "qubit_stark_shift"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, cav_drive, rr_drive, cav_drive2 = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        # cav_drive.play("constant_pulse", ampx=self.y)  # Play continuous pump
        rr_drive.play("gaussian_pulse", ampx=self.y)
        #cav_drive2.play("gaussian_pulse", duration = 750, ampx=self.y) # the duration is same as pi_selective pulse
        qubit.play(self.qubit_op)  # play qubit pi pulse
        qua.align(
            qubit.name, cav_drive.name, rr.name, rr_drive.name
        )  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 48e6
    x_stop = 51e6
    x_step = 0.02e6
    

    amp_start = 0
    amp_stop = 1.4
    amp_step = 0.02

    parameters = {
        "modes": ["QUBIT", "CAV", "RR", "CAV_DRIVE", "RR_DRIVE", "CAV_DRIVE2"],
        "reps": 10000,
        "wait_time": 80e3,  # 4000000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "pi_selective_1",
        "fetch_period": 5,
        "y_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        # "plot_quad": "I_AVG"
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "ylabel": "Pump amplitude scaling",
        "plot_type": "2D",
    }

    experiment = StarkShift(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
