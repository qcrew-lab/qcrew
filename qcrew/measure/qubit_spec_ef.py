"""
A python class describing a qubit two tone spectroscopy measurement using QM,
to find the anharmonicity.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class QubitSpecEf(Experiment):

    name = "qubit_spec_ef"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op1",  # operation used for exciting the qubit from g to e (pi pulse)
        "qubit_op2",  # operation used for exciting the qubit from e to f (CW pulse)
    }

    def __init__(self, qubit_op1, qubit_op2, **other_params):

        self.qubit_op1 = qubit_op1
        self.qubit_op2 = qubit_op2

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq)  # move IF freq to ge resonance
        qubit.play(self.qubit_op1)  # pi pulse to excite qubit from g to e

        # need to check the span to which we can set IF, as it needs to be detuned by about 200 MHz from ge
        qua.update_frequency(qubit.name, -100e6)  # move IF freq to ge resonance
        qubit.play(
            self.qubit_op2
        )  # CW pulse to excite qubit from e to f when resonance is hit

        qua.update_frequency(qubit.name, qubit.int_freq)  # move IF freq to ge resonance
        qubit.play(self.qubit_op1)  # pi pulse to deexcite qubit from e to g

        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 2000,
        "wait_time": 32000,
        # to sweep the qubit if 200MHz - 300 MHz below the ge resonance at -50 MHz. Note that the oscilloscope wont resolve pulses at frequencies over approx. 150MHz properly.
        "x_sweep": (int(-350e6), int(-250e6 + 0.1e6 / 2), int(0.1e6)),
        "qubit_op1": "pi",
        "qubit_op2": "constant_pulse",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = QubitSpecEf(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
