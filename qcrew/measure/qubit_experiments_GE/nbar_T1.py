"""
A python class describing a readout resonator spectroscopy with readout pulse amplitude
sweep using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class nbar_T1(Experiment):

    name = "nbar_T1"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="exp_decay", **other_params):

        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        # (1) Pi-Pulse, (2) new pulse, (3) readout pulse

        qubit.play(self.qubit_op)  # play pi qubit pulse
        # qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.play("constant_pulse", ampx=self.y, duration=self.x)
        rr.measure((self.I, self.Q))  # measure transmitted signal

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 200
    x_stop = 35000
    x_step = 1000

    y_start = 0
    y_stop = 0.1
    y_step = 0.005

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 2000,
        "wait_time": 125000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "pi",
        "single_shot": False,
    }
    plot_parameters = {
        "ylabel": " Pulse Amplitude (V)",
        "xlabel": " Pulse Length (clock cycles)",
        "plot_type": "2D",
        # "zlog" : "True"
    }

    experiment = nbar_T1(**parameters)
    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
