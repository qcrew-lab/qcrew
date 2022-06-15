"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class PowerRabiDDROP(Experiment):

    name = "power_rabi_DDROP"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        qubit_ddrop,
        rr_ddrop,
        steady_state_wait,
        rr_ddrop_freq,
        fit_fn="sine",
        **other_params
    ):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
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
        rr.play(self.rr_ddrop, ampx=1)  # play rr ddrop excitation
        qua.wait(int(self.steady_state_wait // 4), qubit.name)  # wait rr reset
        qubit.play(self.qubit_ddrop, ampx=1)  # play qubit ddrop excitation
        qua.wait(int(self.steady_state_wait // 4), qubit.name)  # wait rr reset
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end

        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
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

    amp_start = -1.8
    amp_stop = 1.8
    amp_step = 0.05

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 200000,
        "wait_time": 2000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "pi_selective3",
        
        "qubit_ddrop": "ddrop_pulse",
        "rr_ddrop": "ddrop_pulse",
        "rr_ddrop_freq": int(-50e6),
        "steady_state_wait": 2000,
        
        # "single_shot": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        # "zlimits": (0.35, 0.5)
    }

    experiment = PowerRabiDDROP(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
