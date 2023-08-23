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


class PowerRabiCastle(Experiment):

    name = "power_rabi_castle"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        cav_op,
        # internal_sweep,
        flux_scaling,
        qubit_delay,
        qubit_delay_2,
        fit_fn="",
        **other_params,
    ):
        self.qubit_op = qubit_op  # pi pulse
        self.cav_op = cav_op  # pi pulse
        self.fit_fn = fit_fn
        # self.internal_sweep = internal_sweep
        self.flux_scaling = flux_scaling
        self.qubit_delay = qubit_delay
        self.qubit_delay_2 = qubit_delay_2
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux, cav = self.modes  # get the modes

        # cav.play(self.cav_op, ampx=1)  # prepare cavity state
        # qua.align(cav.name, flux.name)
        flux.play("castle_IIR_230727_0", ampx=self.flux_scaling)  # to make off resonance
        qua.wait(int((self.qubit_delay) // 4), qubit.name)  # ns
        qubit.play(self.qubit_op, ampx=self.x)  # play pi qubit pulse -109e6
        # qua.wait(int((self.qubit_delay_2 + flux_len) // 4), qubit.name)  # ns
        qubit.play(self.qubit_op, ampx=self.x)  # play pi qubit pulse -109e6
        qua.align(rr.name, qubit.name)
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

    amp_start = -1.05
    amp_stop = 1.05
    amp_step = 0.05
    
    flux_scaling = 0.2955  # 0.5283

    plot_parameters = {
        # "xlabel": "--",
        "xlabel": "Interaction time",
    }

    with Stagehand() as stage:
        flux = stage.FLUX
        flux.operations = {
            f"castle_IIR_230727_0": NumericalPulse(
                path=f"C:/Users/qcrew/Desktop/qcrew/qcrew/config/fast_flux_pulse/castle_superf/castle_IIR_230727_0ns_0dot00_2250.npz",
                I_quad="I_quad",
                Q_quad="Q_quad",
                ampx=1,
            ),
            }

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX", "CAVITY"],
        "reps": 1000000,
        "wait_time": 60000,
        "qubit_op": "gaussian_pi",
        "cav_op": "const_cohstate_1",
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        # "single_shot": True,
        "plot_quad": "I_AVG",
        # "fetch_period": 1,
        "qubit_delay": 350,  # ns
        "qubit_delay_2": 60,  # ns
        # "internal_sweep": flux_len_list,
        "flux_scaling": flux_scaling,
        "fit_fn": "gaussian",
    }

    experiment = PowerRabiCastle(**parameters)
    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
