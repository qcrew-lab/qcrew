"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------
class PowerRabiGRAPE(Experiment):
    name = "power_rabi GRAPE"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, qubit_grape, cav_grape, fit_fn="sine", **other_params):
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.qubit_grape = qubit_grape
        self.cav_grape = cav_grape
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, cav = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq)
        qubit.play(self.qubit_grape, ampx=1)
        cav.play(self.cav_grape, ampx=1)
        qua.align()

        # qua.update_frequency(qubit.name, 176.05e6)

        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse

        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q), ampx=1)
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    amp_start = -1.4
    amp_stop = 1.4
    amp_step = 0.02

    parameters = {
        "modes": ["QUBIT", "RR", "CAV"],
        "reps": 1000,
        "wait_time": 10e6,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "qubit_gaussian_short_pi2_pulse",
        "single_shot": True,
        "cav_grape": "grape_fock1_pulse",
        "qubit_grape": "grape_fock1_pulse",
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        "plot_err": False,
        # "zlimits": (0.35, 0.5)
    }

    experiment = PowerRabiGRAPE(**parameters)
    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
