"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class DDROP(Experiment):

    name = "DDROP_calibration"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_pi",  # qubit pi operation
        "qubit_ddrop",  # qubit pulse used in ddrop algorithm
        "rr_ddrop",  # rr pulse used in ddrop algorithm
        "steady_state_wait",  # Time for resonator to reach steady state
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_pi,
        qubit_ddrop,
        rr_ddrop,
        steady_state_wait,
        rr_ddrop_freq,
        fit_fn=None,
        **other_params
    ):

        self.qubit_pi = qubit_pi
        self.qubit_ddrop = qubit_ddrop
        self.rr_ddrop = rr_ddrop
        self.steady_state_wait = steady_state_wait
        self.rr_ddrop_freq = rr_ddrop_freq
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes
        qubit.play(self.qubit_pi)  # prepare qubit in excited state
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        qua.update_frequency(rr.name, self.rr_ddrop_freq)
        rr.play(self.rr_ddrop)  # play rr ddrop excitation
        qua.wait(
            int(self.steady_state_wait // 4), qubit.name
        )  # wait resonator in steady state
        qubit.play(self.qubit_ddrop, ampx=self.y)  # play qubit ddrop excitation
        qua.wait(
            int(self.steady_state_wait // 4), qubit.name
        )  # wait resonator in steady state
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        qua.update_frequency(rr.name, self.x)
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = 0.0
    amp_stop = 1.85
    amp_step = 0.5

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 50000,
        "wait_time": 500,
        "x_sweep": (int(-53e6), int(-49e6 + 0.1e6 / 2), int(0.1e6)),
        "y_sweep": (0., 1.0, 1.9),
        "qubit_pi": "pi",
        "qubit_ddrop": "ddrop_pulse",
        "rr_ddrop": "ddrop_pulse",
        "rr_ddrop_freq": int(-49.7e6),
        "steady_state_wait": 500,
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        "plot_type": "1D",
    }

    experiment = DDROP(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
