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

    def __init__(self, qubit_op, fit_fn, rr_drive,amp_drive, detuning=0, **other_params):
        self.qubit_op = qubit_op  # half pi pulse
        self.fit_fn = fit_fn
        self.detuning = detuning  # frequency detuning of qubit operation
        self.rr_drive = rr_drive
        self.amp_drive = amp_drive

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """

        factor = qua.declare(qua.fixed)
        qua.assign(factor, self.detuning * 4 * 1e-9)

        qubit, rr = self.modes  # get the modes

        qua.reset_frame(qubit.name)
        rr.play(self.rr_drive, duration=self.y, ampx=self.amp_drive)
        qua.align(rr.name, qubit.name)
        qubit.play(self.qubit_op)  # play half pi qubit pulse

        qua.wait(self.x, qubit.name)  # wait for partial qubit decay

        qua.assign(self.phase, qua.Cast.mul_fixed_by_int(factor, self.x))
        qubit.play(self.qubit_op, phase=self.phase)  # play half pi qubit pulse
        qua.align(qubit.name, rr.name)  # wait last qubit pulse to end
        qua.wait(int(320))
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    
    amplist = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    for amp in amplist:
    
        x_start = 4
        x_stop = 200
        x_step = 1
        detuning_ = 8e6  # 1.12e6

        parameters = {
            "modes": ["QUBIT", "RR"],
            "reps": 1000,
            "wait_time": 500e3,
            "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
            "y_sweep": np.linspace(10, 200, 20, dtype="int").tolist()
            + np.linspace(220, 600, 20, dtype="int").tolist(),
            "qubit_op": "qubit_gaussian_short_pi2_pulse",
            "detuning": int(detuning_),
            "single_shot": True,
            "rr_drive": "constant_drive",
            "fetch_period": 20,
            "amp_drive": amp,
            # "fit_fn": "exp_decay_sine",
            "fit_fn": None,
            "extra_vars": {
                "phase": macros.ExpVariable(
                    var_type=qua.fixed,
                    tag="phase",
                    average=True,
                    buffer=True,
                    save_all=True,
                )
            },
            # "plot_quad": "I_AVG",
            # "fetch_period": 2,
        }

        plot_parameters = {
            "xlabel": "Relaxation time (clock cycles)",
            "plot_err": None,
        }

        experiment = T2(**parameters)
        experiment.name = ("ring-up_Ramsey_ampx0.1times{}_".format(amp))
        
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
