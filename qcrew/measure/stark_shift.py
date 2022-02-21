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

    name = "stark_shift"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",
        "qubit_drive_op",# fit function
    }

    def __init__(self, qubit_op, qubit_drive_op, fit_fn="lorentzian", **other_params):

        self.qubit_op = qubit_op
        self.qubit_drive_detuned = qubit_drive_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, qu_drive = self.modes  # get the modes
        
        qu_drive.play(self.qubit_drive_op, ampx=self.y) # play a detuned tone to the qubit to shift the frequency,
        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 50000,
        "wait_time": 20000,
        "x_sweep": (int(-60e6), int(-40e6), int(0.5e6)),
        "y_sweep": (-1.8, 1.8, 0.1),
        "qubit_op": "constant_pulse",
        "qubit_drive_op": "constant_pulse"
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)", 
    }

    experiment = StarkShift(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
