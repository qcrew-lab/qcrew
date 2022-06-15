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

    def __init__(self, ddrop_params=None, fit_fn=None, **other_params):

        self.ddrop_params = ddrop_params
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        rr, qubit, qubit_ef = self.modes  # get the modes

        #if self.ddrop_params:
        with qua.if_(self.y):
            # macros.DDROP_reset(qubit, rr, **self.ddrop_params)
            # Use qubit_ef if also resetting F state
            macros.DDROP_reset(qubit, rr, **self.ddrop_params, qubit_ef=qubit_ef)

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -55e6
    x_stop = -47e6
    x_step = 0.1e6

    parameters = {
        "modes": ["RR", "QUBIT", "QUBIT_EF"],
        "reps": 5000,
        "wait_time": 100000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (False, True),
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
    }

    ddrop_params = {
        "rr_ddrop_freq": int(-50e6),  # RR IF when playing the RR DDROP pulse
        "rr_steady_wait": 2000,  # in nanoseconds
        "ddrop_pulse": "ddrop_pulse",  # name of all ddrop pulses
    }

    experiment = RRSpecDDROP(ddrop_params=ddrop_params, **parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
