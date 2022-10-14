"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class StarkShift(Experiment):

    name = "qubit_stark_shift_ef"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_pi",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_pi, qubit_ef_op, fit_fn=None, **other_params):

        self.qubit_pi = qubit_pi
        self.fit_fn = fit_fn
        self.qubit_ef_op = qubit_ef_op
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, qubit_drive, qubit_ef = self.modes  # get the modes

        qubit.play(self.qubit_pi)
        qua.align()

        qubit_drive.play("constant_pulse", ampx=self.y)  # Play continuous pump

        qua.wait(int((1000 - 960) / 4), qubit_ef.name)

        qua.update_frequency(qubit_ef.name, self.x)  # update qubit pulse frequency
        qubit_ef.play(self.qubit_ef_op)  # play qubit pi pulse

        qua.align()
        qubit.play(self.qubit_pi)

        # qua.align(qubit_drive.name, rr.name)
        qua.align()
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    amp_start = 0.0
    amp_stop = 1.0
    amp_step = 0.04

    freq_start = -92e6
    freq_stop = -74e6
    freq_step = 0.2e6

    parameters = {
        "modes": ["QUBIT", "RR", "QUBIT_DRIVE", "QUBIT_EF"],
        "reps": 50000,
        "wait_time": 150000,
        "x_sweep": (int(freq_start), int(freq_stop + freq_step / 2), int(freq_step)),
        "qubit_pi": "gaussian_pi_pulse",
        "qubit_ef_op": "gaussian_pi_selective_pulse",
        "fetch_period": 5,
        "y_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "ylabel": "Pump amplitude scaling",
        "plot_type": "2D",
    }

    experiment = StarkShift(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
