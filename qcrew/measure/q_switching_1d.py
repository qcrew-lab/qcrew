"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QSwitch1D(Experiment):

    name = "q_switching_1d"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_drive_detuning, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op  # pi pulse
        self.qubit_drive_detuning = qubit_drive_detuning
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq)
        qubit.play(self.qubit_op)  # play pi qubit pulse
        qua.wait(4, qubit.name, rr.name)
        qua.update_frequency(qubit.name, qubit.int_freq + self.qubit_drive_detuning)
        qua.update_frequency(rr.name, rr.int_freq + self.qubit_drive_detuning + self.x)
        qua.align(rr.name, qubit.name)
        qubit.play("constant_pulse", duration=25000, ampx=0.4)  # play pi qubit pulse
        rr.play("constant_pulse", duration=25000, ampx=0.6)  # play pi qubit pulse
        qua.align(rr.name, qubit.name)
        qua.update_frequency(rr.name, rr.int_freq)
        qua.wait(4, qubit.name, rr.name)
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 1500,
        "wait_time": 400000,
        "x_sweep": (int(-30e6), int(0e6 + 0.2e6 / 2), int(0.2e6)),
        # "y_sweep": (0, 0.6 + 0.1 / 2, 0.1),
        "qubit_op": "pi",
        "qubit_drive_detuning": int(125e6),
        "fetch_period": 2,
    }

    plot_parameters = {
        "xlabel": "Frequency (Hz)",
        # "trace_labels": ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6"],
    }

    experiment = QSwitch1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
