"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import qcrew.measure.qua_macros as macros


# ---------------------------------- Class -------------------------------------
class SelfKerr(Experiment):
    name = "Self_Kerr"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_sel_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "detuning",  # qubit pulse detuning
    }

    def __init__(self, qubit_sel_op, detuning, cav_op, fit_fn=None, **other_params):
        self.qubit_sel_op = qubit_sel_op
        self.cav_op = cav_op
        self.fit_fn = fit_fn
        self.detuning = detuning
        # self.detuning = detuning  # frequency detuning of qubit operation

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        factor = qua.declare(qua.fixed)
        qua.assign(factor, self.detuning * 4 * 1e-9)

        qua.reset_frame(cav.name)

        cav.play(self.cav_op, ampx=self.y)  # displace cavity
        qua.wait(self.x, cav.name)  # wait for self-kerr to dephase cavity

        qua.assign(self.phase, qua.Cast.mul_fixed_by_int(factor, self.x))

        cav.play(self.cav_op, ampx=self.y, phase= self.phase + 0.5)  # displace cavity back
        qua.align(qubit.name, cav.name)
        qubit.play(self.qubit_sel_op)  # flip qubit if cavity in vacuum
        qua.align(qubit.name, rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    wait_start = 10000
    wait_stop = 30000
    wait_step = 100

    detuning_ = 10e3  # 1.12e6

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 80,
        "wait_time": 10e6,
        "x_sweep": (
            int(wait_start),
            int(wait_stop + wait_step / 2),
            int(wait_step),
        ),
        "y_sweep":[0.5, 1.0, 1.5, 2.0],
        # "y_sweep": [2.0],
        "detuning": int(detuning_),
        "qubit_sel_op": "qubit_gaussian_sel_pi_pulse",
        "cav_op": "coherent_1_long",
        # "plot_quad": "I_AVG",
        "fetch_period": 8,
        # "fit_fn": "gaussian",
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
        "plot_err": False,
        "plot_type": "1D",
    }

    experiment = SelfKerr(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
