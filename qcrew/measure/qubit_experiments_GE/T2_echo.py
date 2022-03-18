"""
A python class describing a T2 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class T2_Echo(Experiment):

    name = "T2_echo"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_pi2",  # operation used for exciting the qubit
        "qubit_pi",
        "fit_fn",  # fit function
        "detuning",  # qubit pulse detuning
    }

    def __init__(
        self, qubit_pi2, qubit_pi, detuning=0, fit_fn="exp_decay_sine", **other_params
    ):

        self.qubit_pi2 = qubit_pi2
        self.qubit_pi = qubit_pi  # half pi pulse
        self.fit_fn = fit_fn
        self.detuning = detuning  # frequency detuning of qubit operation

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes
        qua.update_frequency(qubit.name, qubit.int_freq + self.detuning)  # detune
        qubit.play(self.qubit_pi2)  # play half pi qubit pulse
        qua.wait(self.x / 2, qubit.name)  # wait for partial qubit decay
        qubit.play(self.qubit_pi)  # play pi qubit pulse
        qua.wait(self.x / 2, qubit.name)  # wait for partial qubit decay
        qubit.play(self.qubit_pi2)  # play half pi qubit pulse
        qua.align(qubit.name, rr.name)  # wait last qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 10
    x_stop = 60000
    x_step = 800

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 10000,
        "wait_time": 200000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_pi2": "pi2",
        "qubit_pi": "pi",
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = T2_Echo(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
