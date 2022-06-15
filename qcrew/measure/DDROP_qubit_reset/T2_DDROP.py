"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class T2DDROP(Experiment):

    name = "T2_DDROP"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        detuning,
        qubit_ddrop,
        rr_ddrop,
        steady_state_wait,
        rr_ddrop_freq,
        fit_fn="exp_decay_sine",
        **other_params
    ):

        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        self.detuning = detuning
        self.qubit_ddrop = qubit_ddrop
        self.rr_ddrop = rr_ddrop
        self.steady_state_wait = steady_state_wait
        self.rr_ddrop_freq = rr_ddrop_freq

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(rr.name, self.rr_ddrop_freq)
        rr.play(self.rr_ddrop, ampx=0)  # play rr ddrop excitation
        qua.wait(int(self.steady_state_wait // 4), qubit.name)  # wait rr reset
        qubit.play(self.qubit_ddrop, ampx=0)  # play qubit ddrop excitation
        qua.wait(int(self.steady_state_wait // 4), qubit.name)  # wait rr reset
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end

        qua.update_frequency(qubit.name, qubit.int_freq + self.detuning)  # detune
        qubit.play(self.qubit_op)  # play half pi qubit pulse
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qubit.play(self.qubit_op)  # play half pi qubit pulse
        qua.align(qubit.name, rr.name)  # wait last qubit pulse to end
        qua.update_frequency(rr.name, rr.int_freq)
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 4
    x_stop = 5e3
    x_step = 25
    detuning = 300e3

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 200000,
        "wait_time": 50000,
        "detuning": int(detuning),
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "pi2",
        "qubit_ddrop": "ddrop_pulse",
        "rr_ddrop": "ddrop_pulse",
        "rr_ddrop_freq": int(-50e6),
        "steady_state_wait": 2000,
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = T2DDROP(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
