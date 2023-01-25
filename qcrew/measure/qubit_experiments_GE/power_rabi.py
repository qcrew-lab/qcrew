"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
import qcrew.measure.qua_macros as macros
from qm import qua

from qcrew.measure.qua_macros import *

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
        # self.internal_sweep = ["first", "second"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, cav = self.modes  # get the modes
        qua.reset_frame(qubit.name)

        if 0:
            rr.measure((self.I, self.Q))  # measure transmitted signal
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()  # align measurement
            qua.wait(int(50))

            if self.ddrop_params:
                macros.DDROP_reset(qubit, rr, **self.ddrop_params)
                # Use qubit_ef if also resetting F state
                # macros.DDROP_reset(qubit, rr, **self.ddrop_params, qubit_ef=qubit_ef)

            qua.align()

        num = 8
        for n in range(num):
            qua.align()
            qubit.play(self.qubit_op, ampx=self.x, phase=0.0)  # if checking a pi2 pulse
            qua.align()
            # qubit.play(self.qubit_op, ampx=self.x, phase=0.0)  # if checking a pi2 pulse
            # qua.align()

        qua.align()  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        # if self.single_shot:  # assign state to G or E
        #     temp = (self.I < 0) & (self.Q > 0)
        #     qua.assign(self.state, qua.Cast.to_fixed(temp))

        qua.wait(int(self.wait_time // 4))  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

<<<<<<< Updated upstream
    amp_start = -1.1
    amp_stop = 1.1
=======
    amp_start = -1.4
    amp_stop = 1.4
>>>>>>> Stashed changes
    amp_step = 0.05
    parameters = {
<<<<<<< Updated upstream
        "modes": ["QUBIT", "RR", "CAV"],
        "reps": 4000,
        "wait_time": 100e3,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        # "y_sweep": [0.0,1,],
        "qubit_op": "pi2",  # constant_cos_pi
        "single_shot": True,
        "fetch_period": 2,
        # "plot_quad": "I_AVG",
=======
        "modes": ["QUBIT", "RR"],
        "reps": 200000,
        "wait_time": 40000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "constant_pi_pulse3",  # "gaussian_pi_selective_pulse3",
        "single_shot": False,
        "plot_quad": "Z_AVG",
>>>>>>> Stashed changes
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        "skip_plot": False,
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
