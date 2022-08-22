"""
A python class describing a T2 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from cmath import phase
from re import X
from typing import ClassVar

from betterproto import T

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import qcrew.measure.qua_macros as macros

import numpy as np

# ---------------------------------- Class -------------------------------------


class T2(Experiment):

    name = "T2"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "detuning",  # qubit pulse detuning
    }

    def __init__(
        self,
        qubit_op,
        ddrop_params=None,
        detuning=0,
        fit_fn="exp_decay_sine",
        **other_params
    ):

        self.qubit_op = qubit_op  # half pi pulse
        self.fit_fn = fit_fn
        self.detuning = detuning  # frequency detuning of qubit operation
        self.ddrop_params = ddrop_params

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """

        qubit, rr, qubit_ef = self.modes  # get the modes

        # if self.ddrop_params:
        #     # macros.DDROP_reset(qubit, rr, **self.ddrop_params)
        #     # Use qubit_ef if also resetting F state
        #     macros.DDROP_reset(qubit, rr, **self.ddrop_params, qubit_ef=qubit_ef)

        factor = qua.declare(qua.fixed)
        qua.assign(factor, self.detuning * 4 * 1e-9)

        qua.reset_frame(qubit.name)
        qua.align()
        qubit.play(self.qubit_op)  # play half pi qubit pulse
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qua.assign(self.phase, qua.Cast.mul_fixed_by_int(factor, self.x))
        qubit.play(self.qubit_op, phase=self.phase)  # play half pi qubit pulse
        qua.align()  # wait last qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = 4
    x_stop = 4000
    x_step = 50
    detuning_ = 400e3  # 1.12e6

    parameters = {
        "modes": ["QUBIT", "RR", "QUBIT_EF"],
        "reps": 5000,
        "wait_time": 80000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "constant_cos_pi2",
        "detuning": int(detuning_),
        "extra_vars": {
            "phase": macros.ExpVariable(
                var_type=qua.fixed,
                tag="phase",
                average=True,
                buffer=True,
                save_all=True,
            )
        },
        "single_shot": False,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    ddrop_params = {
        "rr_ddrop_freq": int(-50.4e6),  # RR IF when playing the RR DDROP pulse
        "rr_steady_wait": 2000,  # in nanoseconds
        "ddrop_pulse": "ddrop_pulse",  # name of all ddrop pulses
    }

    experiment = T2(ddrop_params=ddrop_params, **parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
