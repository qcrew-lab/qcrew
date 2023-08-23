"""
A python class describing a cavity spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np

# ---------------------------------- Class -------------------------------------


class FluxPhaseGate(Experiment):

    name = "flux_phase_gate"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="sine", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.internal_sweep = [20, 28, 36]  # np.arange(20, 120, 8)
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        qua.reset_frame(qubit.name)
        for pulse_length in self.internal_sweep:
            # pulse_length = 4
            qubit.play(self.qubit_op, phase=0)  # play pi2 qubit pulse
            qua.align(qubit.name, flux.name)
            flux.play(f"square_{pulse_length}ns_ApBpC", ampx=0.61)
            qua.wait(
                int((pulse_length + 80) // 4), qubit.name
            )  # wait for the end of the flux pulse
            qubit.play(self.qubit_op, phase=self.x)  # play pi2 qubit pulse
            qua.align(rr.name, qubit.name)  # align all modes
            rr.measure((self.I, self.Q))  # measure transmitted signal
            qua.wait(int(self.wait_time // 4))  # wait system reset

            if self.single_shot:  # assign state to G or E
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )

            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()


# -------------------------------- Execution -----------------------------------


if __name__ == "__main__":

    x_start = 0.0
    x_stop = 1.0
    x_step = 0.05
    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 20000,
        "wait_time": 80e3,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_op": "gaussian_pi2",
        "fetch_period": 1,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Phase of second pi pulse (1/2pi rad)",
        # "plot_type": "2D",
    }

    experiment = FluxPhaseGate(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
