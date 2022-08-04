"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class DDROPRRCal(Experiment):

    name = "DDROP_rr_cal"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "rr_ddrop_freq",
        "rr_steady_wait",  # Time for resonator to reach steady state
        "ddrop_pulse",  # qubit and rr pulse names used in ddrop algorithm
        "fit_fn",  # fit function
    }

    def __init__(
        self, rr_ddrop_freq, rr_steady_wait, ddrop_pulse, fit_fn="sine", **other_params
    ):
        self.rr_ddrop_freq = rr_ddrop_freq
        self.rr_steady_wait = rr_steady_wait
        self.ddrop_pulse = ddrop_pulse
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        # Play RR ddrop pulse
        qua.update_frequency(rr.name, self.rr_ddrop_freq)
        rr.play(self.ddrop_pulse, ampx=self.y)

        # Play qubit ddrop pulse
        qua.wait(int(self.rr_steady_wait // 4), qubit.name)  # wait steady state of rr
        qubit.play(self.ddrop_pulse, self.x)
        qua.wait(int(self.rr_steady_wait // 4), qubit.name)  # wait steady state of rr
        qua.align(qubit.name, rr.name)  # wait pulses to end

        qua.update_frequency(rr.name, rr.int_freq)
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1
    amp_stop = 0
    amp_step = 0.01

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 50000,
        "wait_time": 100000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "y_sweep": (
            0.2,
            0.3,
            0.4,
        ),
        "ddrop_pulse": "ddrop_pulse",
        "rr_ddrop_freq": int(-50.13e6),
        "rr_steady_wait": 2000,
        "single_shot": False,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        "plot_type": "1D",
    }

    experiment = DDROPRRCal(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
