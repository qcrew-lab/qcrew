"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class ResonantCtrlFastFluxT1(Experiment):

    name = "resonant_ctrl_T1"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, pi_01m, sel_pi_fock1, fit_fn="exp_decay", **other_params):

        self.pi_01m = pi_01m
        self.fit_fn = fit_fn
        self.sel_pi_fock1 = sel_pi_fock1

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes

        #prepare fock state 1
        flux.play("predist_pulse_2", ampx=-0.247)
        qua.wait(50, qubit.name)
        qua.update_frequency(qubit.name, int(-57.84e6))
        qubit.play(self.pi_01m, ampx=1)  # play pi pulse to (g,0)->(1,-)

        qua.wait(self.x, qubit.name)  # wait relaxation
        # flip qubit when fock state at 1
        qua.update_frequency(qubit.name, int(-89.59e6))
        qubit.play(self.sel_pi_fock1, ampx=1)  # play pi pulse to (g,0)->(1,-)
        
        # readout
        qua.align(rr.name, qubit.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 200
    x_stop = 10e3
    x_step = 100

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 100000,
        "wait_time": 10e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        # "y_sweep": (0.0, 1.0),
        # "qubit_op": "constant_pi",
        "pi_01m": "gaussian_sel_pi2_01m",
        "sel_pi_fock1": "gaussian_sel_pi_fock1",
        # "plot_quad": "I_AVG",
        "fit_fn": "exp_decay",
        "fetch_period":5
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = ResonantCtrlFastFluxT1(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
