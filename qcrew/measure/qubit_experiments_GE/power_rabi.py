"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
import qcrew.measure.qua_macros as macros
from qm import qua


# ---------------------------------- Class -------------------------------------


class PowerRabi(Experiment):

    name = "power_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, ddrop_params=None, fit_fn="sine", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.ddrop_params = ddrop_params

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, qubit_ef = self.modes  # get the modes

        if self.ddrop_params:
            macros.DDROP_reset(qubit, rr, **self.ddrop_params)
            # Use qubit_ef if also resetting F state
            # macros.DDROP_reset(qubit, rr, **self.ddrop_params, qubit_ef=qubit_ef)

        qua.align()

        qubit.play(self.qubit_op, ampx=self.x, phase=0)  # if checking a pi2 pulse
        qubit.play(self.qubit_op, ampx=self.x, phase=0)  # if checking a pi2 pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4))  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1.2
    amp_stop = 1.2
    amp_step = 0.05
    parameters = {
        "modes": ["QUBIT", "RR", "QUBIT_EF"],
        "reps": 5000,
        "wait_time": 100000,  # 2000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "oct_pulse", #constant_cos_pi
        # "single_shot": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
    }

    ddrop_params = {
        "rr_ddrop_freq": int(-49.8e6),  # RR IF when playing the RR DDROP pulse
        "rr_steady_wait": 2000,  # in nanoseconds
        "ddrop_pulse": "ddrop_pulse",  # name of all ddrop pulses
    }

    # experiment = PowerRabi(**parameters, ddrop_params=ddrop_params)
    experiment = PowerRabi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
