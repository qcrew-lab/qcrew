"""
A python class describing a readout resonator spectroscopy with qubit in ground and 
excited state using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.measure.experiment import Experiment
import qcrew.measure.qua_macros as macros
from qm import qua

# ---------------------------------- Class -------------------------------------


class RRSpecDDROP(Experiment):

    name = "rr_spec_DDROP"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(
        self, rr_ddrop_freq, ddrop_pulse, rr_steady_wait, fit_fn=None, **other_params
    ):

        self.ddrop_pulse = ddrop_pulse
        self.rr_steady_wait = rr_steady_wait
        self.rr_ddrop_freq = rr_ddrop_freq
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        rr, qubit = self.modes  # get the modes

        # qubit.play("gaussian_pi")
        # qua.align()

        # Play RR ddrop pulse
        qua.update_frequency(rr.name, self.rr_ddrop_freq)
        rr.play(self.ddrop_pulse, ampx = self.y)
        # Play qubit ddrop pulse
        qua.wait(int(self.rr_steady_wait // 4), qubit.name)  # wait steady state of rr
        qubit.play(self.ddrop_pulse, ampx = self.y)
        qua.wait(int(self.rr_steady_wait // 4), qubit.name)  # wait steady state of rr
        qua.align(qubit.name, rr.name)  # wait pulses to end

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -52.5e6
    x_stop = -49e6
    x_step = 0.05e6

    parameters = {
        "modes": ["RR", "QUBIT"],
        "reps": 5000,
        "wait_time": 60000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (0., 1.),
        "plot_quad": "Z_AVG",
        "rr_ddrop_freq": int(-50e6),  # RR IF when playing the RR DDROP pulse
        "rr_steady_wait": 3000,  # in nanoseconds
        "ddrop_pulse": "ddrop_pulse",  # name of all ddrop pulses
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
    }

    experiment = RRSpecDDROP(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
