"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------
# delete this comment


class T1_GRAPE(Experiment):
    name = "T1"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, qubit_grape, cav_grape, fit_fn="exp_decay", **other_params
    ):
        self.qubit_op = qubit_op  # pi pulse
        self.qubit_grape = qubit_grape
        self.cav_grape = cav_grape
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, cav = self.modes  # get the modes

        qubit.play(self.qubit_grape)
        cav.play(self.cav_grape)
        qua.align()

        # qubit.play(self.qubit_op)  # play pi qubit pulse
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
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
    x_stop = 150_000  # Clock cycles
    x_step = 2000

    parameters = {
        "modes": ["QUBIT", "RR", "CAV"],
        "reps": 10000,
        "wait_time": 10e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "qubit_gaussian_short_pi_pulse",
        "qubit_grape": "grape_fock8_pulse",
        "cav_grape": "grape_fock8_pulse",
        "single_shot": True,
        "plot_quad": "I_AVG",
        "fetch_period": 4,
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
        # "plot_err": None,
    }

    experiment = T1_GRAPE(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
