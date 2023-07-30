"""
A python class describing a flux pulse spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class PiPulseScope(Experiment):

    name = "pi_pulse_scope"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "flux_op",
        "flux_delay",
        "rr_delay",
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, flux_op, flux_delay, rr_delay, fit_fn=None, **other_params
    ):

        self.qubit_op = qubit_op
        self.flux_op = flux_op
        self.flux_delay = flux_delay
        self.rr_delay = rr_delay
        self.fit_fn = fit_fn
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, flux, rr = self.modes  # get the modes
        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qua.wait(self.y, qubit.name)
        qubit.play(self.qubit_op, ampx=1)  # play qubit pulse
        qua.wait(int(self.flux_delay // 4), flux.name)  # ns, buffer time for pi pulse
        flux.play(self.flux_op, ampx=0.6)
        qua.wait(int(self.rr_delay // 4), rr.name)  # ns
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.align()
        qua.wait(int(self.wait_time // 4), flux.name)  # wait system reset

        # if self.single_shot:  # assign state to G or E
        #     qua.assign(
        #         self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
        #     )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -200e6  # 181.25e6
    x_stop = -85e6  # 181.5 e6
    x_step = 2.0e6

    y_start = 880  # cc
    y_stop = 1300
    y_step = 5

    parameters = {
        "modes": ["QUBIT", "FLUX", "RR"],
        "reps": 5000,
        "wait_time": 60000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        "flux_delay": 40,  # ns
        "rr_delay": 5600,  # ns
        "qubit_op": "constant_pi_16ns",
        "flux_op": "castle_IIR_230727_396ns_0dot00",  # "castle_96",
        "fetch_period": 5,
        # "single_shot": True,
        "plot_quad": "I_AVG",
        # "fit_fn": "gaussian",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "ylabel": "Delay (Clock Cycles)",
        "plot_type": "2D",
        # "cmap": "inferno",
    }

    experiment = PiPulseScope(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
