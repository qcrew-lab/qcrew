"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class PowerRabi_FF_fock_1(Experiment):

    name = "power_rabi_ff_fock_1"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op2, qubit_op, fit_fn="sine", **other_params):

        self.qubit_op = qubit_op
        self.qubit_op2 = qubit_op2
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        
        # prepare fock state 1
        flux.play("predist_pulse_2", ampx=-0.247)
        qua.wait(50, qubit.name)
        qua.update_frequency(qubit.name, int(-57.84e6))
        qubit.play(self.qubit_op, ampx=1)  # play pi pulse to (g,0)->(1,-)
        
        # flip qubit when fock state at 1
        qua.update_frequency(qubit.name, int(-89.59e6))
        qubit.play(self.qubit_op2, ampx=self.x)  # play qubit pulse
        qua.align(flux.name, qubit.name)  # wait flux pulse to end
        
        qua.align(rr.name, qubit.name)  # wait qubit pulse to end
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
    amp_step = 0.1
    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 1000000,
        "wait_time": 100000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "gaussian_sel_pi_01m",
        "qubit_op2": "gaussian_sel_pi_fock1",
        "single_shot": False,
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
    }

    experiment = PowerRabi_FF_fock_1(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
