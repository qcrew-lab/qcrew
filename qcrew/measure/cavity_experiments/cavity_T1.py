"""
A python class describing a cavity T1 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class CavityT1(Experiment):
    name = "cavity_T1"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn, **other_params):
        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        cav.play(self.cav_op, ampx=1.0)  # play displacement to cavity
        qua.wait(self.x, cav.name)  # wait relaxation
        qua.align(cav.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align all modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 16
    x_stop = 5000e3
    x_step = 20e3
    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 10000,
        "wait_time": 10e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "qubit_gaussian_sel_pi_pulse",
        "cav_op": "coherent_4_long",
        # "plot_quad": "I_AVG",
        # "fit_fn": None,
        "single_shot": True, 
        "fit_fn": "cohstate_decay",
        "fetch_period": 8,
    }

    plot_parameters = {
        "xlabel": "Cavity relaxation time (clock cycles)",
        "plot_err": None,
    }

    experiment = CavityT1(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
