"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class DDROPQubitCal(Experiment):

    name = "DDROP_qubit_cal"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_pi",  # qubit pi operation
        "rr_steady_wait",  # Time for resonator to reach steady state
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_pi,
        rr_ddrop_freq,
        rr_steady_wait,
        ddrop_pulse,
        fit_fn=None,
        **other_params
    ):
        self.rr_ddrop_freq = rr_ddrop_freq
        self.rr_steady_wait = rr_steady_wait
        self.ddrop_pulse = ddrop_pulse
        self.qubit_pi = qubit_pi
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        # Excite qubit
        qubit.play(self.qubit_pi)  # prepare qubit in excited state

        qua.align(qubit.name, rr.name)

        # Play RR ddrop pulse
        qua.update_frequency(rr.name, self.rr_ddrop_freq)
        rr.play(self.ddrop_pulse)

        # Play qubit ddrop pulse
        qua.wait(int(self.rr_steady_wait // 4), qubit.name)  # wait steady state of rr
        qubit.play(self.ddrop_pulse, ampx = self.x) 
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

    amp_start = 0.0
    amp_stop = 1.9
    amp_step = 0.02

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 5000,
        "wait_time": 325000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_pi": "pi",
        "ddrop_pulse": "ddrop_pulse",
        "rr_ddrop_freq": int(-50.3e6),
        "rr_steady_wait": 1000,
        "single_shot": False,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        "plot_type": "1D",
    }

    experiment = DDROPQubitCal(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
