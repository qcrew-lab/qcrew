"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QSwitch2D(Experiment):

    name = "q_switching_2D"

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

        qua.update_frequency(qubit.name, qubit.int_freq + self.qubit_drive_detuning)
        qua.update_frequency(rr.name, rr.int_freq + self.qubit_drive_detuning + self.y)
        qua.align(rr.name, qubit.name)
        qubit.play("constant_pulse", duration=4000)  # play pi qubit pulse
        rr.play("constant_pulse", duration=4000)  # play pi qubit pulse
        qua.align(rr.name, qubit.name)
        qua.update_frequency(rr.name, rr.int_freq)
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 5000,
        "wait_time": 400000,
        "x_sweep": (int(16), int(20e3 + 1000 / 2), int(1000)),
        "y_sweep": (int(-25e6), int(-10e6 + 0.1e6 / 2), int(0.1e6)),
        "qubit_op": "pi",
        "qubit_drive_detuning": int(120e6),
        "fetch_period": 2,
    }

    plot_parameters = {
        "xlabel": "Frequency (Hz)",
    }

    experiment = QSwitch1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
