"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
import qcrew.measure.qua_macros as macros
from qm import qua

# ---------------------------------- Class -------------------------------------


class T1DDROP(Experiment):

    name = "T1_DDROP"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, ddrop_params = None, fit_fn="exp_decay", **other_params):

        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        self.ddrop_params = ddrop_params

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        if self.ddrop_params:
            macros.DDROP_reset(qubit, rr, **self.ddrop_params)
            # Use qubit_ef if also resetting F state
            # macros.DDROP_reset(qubit, rr, **self.ddrop_params, qubit_ef = qubit_ef)

        qubit.play(self.qubit_op)  # play pi qubit pulse
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        qua.update_frequency(rr.name, rr.int_freq)
        rr.measure((self.I, self.Q))  # measure qubit state

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 4
    x_stop = 25e3
    x_step = 300

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 200000,
        "wait_time": 2000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "pi_selective3",
        "qubit_ddrop": "ddrop_pulse",
        "rr_ddrop": "ddrop_pulse",
        "rr_ddrop_freq": int(-50e6),
        "steady_state_wait": 2000,
        "single_shot": False,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }
    
    ddrop_params = {
        "rr_ddrop_freq": int(-50e6),         # RR IF when playing the RR DDROP pulse
        "rr_steady_wait": 2000,              # in nanoseconds
        "ddrop_pulse": "ddrop_pulse",        # name of all ddrop pulses
    }

    experiment = T1DDROP(ddrop_params = ddrop_params, **parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
