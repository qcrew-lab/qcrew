"""
A python class describing a vacuum rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qcrew.control import Stagehand
from qcrew.control.pulses.numerical_pulse import NumericalPulse
from qcrew.analyze import fit
from qm import qua

import numpy as np
import h5py

# ---------------------------------- Class -------------------------------------


class VacuumRabi1D(Experiment):

    name = "vacuum_rabi_castle_1d_duration"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        internal_sweep,
        flux_scaling,
        fit_fn="",
        **other_params,
    ):
        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        self.internal_sweep = internal_sweep
        self.flux_scaling = flux_scaling
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        for flux_len in self.internal_sweep:
            flux.play(f"castle_IIR_230727_{flux_len}", ampx=self.flux_scaling)  # ns
            qua.wait(int((250) // 4), rr.name, qubit.name)  # ns
            qubit.play(self.qubit_op)  # play pi qubit pulse -109e6
            qua.wait(int((920) // 4), rr.name)
            rr.measure((self.I, self.Q))  # measure qubit state
            if self.single_shot:  # assign state to G or E7
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )
            qua.wait(int(self.wait_time // 4))  # wait system reset
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    flux_scaling = 0.574
    # flux_amp_list = np.arange(-0.12, 0.12, 0.01)
    flux_len_list = np.arange(60, 100, 4)

    plot_parameters = {
        "xlabel": "--",
        # "plot_type": "2D",
    }

    with Stagehand() as stage:
        flux = stage.FLUX
        for flux_len in flux_len_list:
            flux.operations = {
                f"castle_IIR_230727_{flux_len}": NumericalPulse(
                    path=f"C:/Users/qcrew/Desktop/qcrew/qcrew/config/fast_flux_pulse/castle_1d/castle_IIR_230727_{flux_len}ns_0dot04_2250.npz",
                    I_quad="I_quad",
                    Q_quad="Q_quad",
                    ampx=1,
                ),
            }

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 8000,
        "wait_time": 1.25e6,
        "qubit_op": "gaussian_pi",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        "fetch_period": 20,
        "internal_sweep": flux_len_list,
        "flux_scaling": flux_scaling,
        "fit_fn": "gaussian",
    }

    experiment = VacuumRabi1D(**parameters)
    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
