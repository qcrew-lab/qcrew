"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class CondPowerRabi(Experiment):

    name = "conditional_power_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "resonator_op",  # operation used for exciting the RR
        "steady_state_wait",  # Time for resonator to reach steady state
        "rr_ddrop_freq",
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        resonator_op,
        steady_state_wait,
        rr_ddrop_freq,
        fit_fn="sine",
        **other_params
    ):
        self.qubit_op = qubit_op
        self.resonator_op = resonator_op
        self.rr_ddrop_freq = rr_ddrop_freq
        self.steady_state_wait = steady_state_wait
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes
        qua.update_frequency(rr.name, self.rr_ddrop_freq)
        rr.play(self.resonator_op, ampx=self.y)  # play a long rr excitation
        qua.wait(
            int(self.steady_state_wait // 4), qubit.name
        )  # wait resonator in steady state
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse concomitantly
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        qua.update_frequency(rr.name, rr.int_freq)
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1
    amp_stop = 0
    amp_step = 0.001

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 50000,
        "wait_time": 100000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "y_sweep": (0.0, 0.02, 0.08),
        "qubit_op": "ddrop_pulse",
        "resonator_op": "ddrop_pulse",
        "rr_ddrop_freq": int(-50.4e6),
        "steady_state_wait": 2000,
        "single_shot": True,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        "plot_type": "1D",
    }

    experiment = CondPowerRabi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
