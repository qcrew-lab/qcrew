"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
import qcrew.measure.qua_macros as macros
from qm import qua

# ---------------------------------- Class -------------------------------------


class Ramseyrevival(Experiment):
    name = "Ramsey_revival"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "detuning",
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, cav_op, detuning, cavity_amp, fit_fn=None, **other_params
    ):
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.cavity_amp = cavity_amp
        self.fit_fn = fit_fn
        self.detuning = detuning  # frequency detuning of qubit operation

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        # factor = qua.declare(qua.fixed)
        # qua.assign(factor, self.detuning * 4 * 1e-9)
        # qua.reset_frame(qubit.name)

        cav.play(self.cav_op, self.cavity_amp)  # prepare cavity state
        qua.align(cav.name, qubit.name)  # align modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.wait(self.x, qubit.name)
        # qua.assign(self.phase, qua.Cast.mul_fixed_by_int(factor, self.x))

        qubit.play(self.qubit_op, phase=self.phase)  # play  qubit pulse with pi/2
        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 300
    x_stop = 400
    x_step = 4
    # x_start = 300
    # x_stop = 400
    # x_step = 1

    detuning_ = 0e6

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 200,
        "wait_time": 16e6,
        "cavity_amp": 3.0,
        "detuning": int(detuning_),
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "qubit_gaussian_64ns_pi2_pulse",
        "cav_op": "coherent_1_long",
        # "plot_quad": "I_AVG",
        "fetch_period": 8,
        "fit_fn": "gaussian",
        "single_shot": True,
        "extra_vars": {
            "phase": macros.ExpVariable(
                var_type=qua.fixed,
                tag="phase",
                average=True,
                buffer=True,
                save_all=True,
            )
        },
    }

    plot_parameters = {
        "xlabel": "Wait time (clock)",
        # "plot_err": False,
        # "plot_type": "1D",
    }

    experiment = Ramseyrevival(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
