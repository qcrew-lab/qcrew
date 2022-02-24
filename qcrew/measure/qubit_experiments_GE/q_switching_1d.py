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
        qubit, rr, qdrive = self.modes  # get the modes

        # qua.update_frequency(qubit.name, qubit.int_freq)
        qubit.play(self.qubit_op)  # play pi qubit pulse
        # qua.wait(4, qubit.name, rr.name)
        # qua.update_frequency(qubit.name, qubit.int_freq + self.qubit_drive_detuning)
        qua.update_frequency(rr.name, rr.int_freq + self.qubit_drive_detuning + self.x)
        qua.align(rr.name, qubit.name, qdrive.name)
        qdrive.play(
            "constant_pulse", duration=5000, ampx=0.1
        )  # qswitch pumps, note this duration is also in clock cycles, not ns
        rr.play("constant_pulse", duration=5000, ampx=0.2)  # qswitch pumps
        qua.align(rr.name, qubit.name, qdrive.name)
        qua.update_frequency(rr.name, rr.int_freq)
        qua.wait(4, qubit.name, rr.name, qdrive.name)
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -10e6
    x_stop = 0e6
    x_step = 0.1e6

    parameters = {
        "modes": ["QUBIT", "RR", "QUBIT_DRIVE"],
        "reps": 50000,
        "wait_time": 200000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "pi",
        "qubit_drive_detuning": int(40e6),
        "fetch_period": 1,
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Frequency (Hz)",
    }

    experiment = QSwitch1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
