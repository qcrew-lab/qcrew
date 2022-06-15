"""
A python class describing a ef power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class QubitPopulation(Experiment):

    name = "qubit_population_DDROP"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_ge_pi",
        "qubit_ef_pi",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_ge_pi,
        qubit_ef_pi,
        qubit_ddrop,
        rr_ddrop,
        steady_state_wait,
        rr_ddrop_freq,
        ef_int_freq,
        fit_fn="sine",
        **other_params
    ):

        self.qubit_ge_pi = qubit_ge_pi
        self.fit_fn = fit_fn
        self.qubit_ef_pi = qubit_ef_pi
        self.qubit_ddrop = qubit_ddrop
        self.rr_ddrop = rr_ddrop
        self.steady_state_wait = steady_state_wait
        self.rr_ddrop_freq = rr_ddrop_freq
        self.ef_int_freq = ef_int_freq

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(rr.name, self.rr_ddrop_freq)
        rr.play(self.rr_ddrop)  # play rr ddrop excitation
        qua.wait(int(self.steady_state_wait // 4), qubit.name)  # wait rr reset
        qubit.play(self.qubit_ddrop)  # play qubit ddrop excitation
        qua.wait(int(self.steady_state_wait // 4), qubit.name)  # wait rr reset

        qubit.play(self.qubit_ge_pi, ampx=self.y)
        qua.update_frequency(qubit.name, self.ef_int_freq)
        qubit.play(self.qubit_ef_pi, ampx=self.x)  # e-> f
        qua.update_frequency(qubit.name, qubit.int_freq)
        qubit.play(self.qubit_ge_pi)  # e-> g

        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        qua.update_frequency(rr.name, rr.int_freq)  # update resonator pulse frequency
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1.8
    amp_stop = 1.8
    amp_step = 0.05

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 200000,
        "wait_time": 2000,
        "ef_int_freq": int(-57e6),
        "qubit_ge_pi": "pi",
        "qubit_ef_pi": "pi_ef",
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "y_sweep": [0.0, 1.0],
        "qubit_ddrop": "ddrop_pulse",
        "rr_ddrop": "ddrop_pulse",
        "rr_ddrop_freq": int(-50e6),
        "steady_state_wait": 1000,
        "single_shot": False,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
    }

    experiment = QubitPopulation(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
