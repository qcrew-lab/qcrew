"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np


# ---------------------------------- Class -------------------------------------
class NSplitSpectroscopy(Experiment):
    name = "number_split_spec_grape"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        cav_op,
        cav_grape,
        qubit_grape,
        cav_amp,
        fit_fn=None,
        **other_params
    ):
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.cav_grape = cav_grape
        self.qubit_grape = qubit_grape
        self.cav_amp = cav_amp
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.update_frequency(qubit.name, qubit.int_freq)
        if self.cav_grape == "vacuum":
            pass
        elif self.cav_grape == "coh1":
            cav.play(self.cav_op, ampx=(1, 0, 0, 1), phase=-0.25)
        else:
            qubit.play(self.qubit_grape)
            cav.play(self.cav_grape)

        qua.align()

        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    pulselist = [
        "vacuum",
        "grape_fock1_pulse",
        "grape_fock2_pulse",
        "grape_fock3_pulse",
        "grape_fock4_pulse",
        "grape_fock5_pulse",
        "grape_fock6_pulse",
        "grape_fock7_pulse",
        "grape_fock8_pulse",
        "grape_fock01_pulse",
        "grape_fock0i1_pulse",
        "grape_fock02_pulse",
        "grape_fock0i2_pulse",
        "grape_fock03_pulse",
        "grape_fock0i3_pulse",
        "grape_fock04_pulse",
        "grape_fock0i4_pulse",
        "grape_fock05_pulse",
        "grape_fock0i5_pulse",
        "grape_fock12_pulse",
        "grape_fock1i2_pulse",
        "grape_fock13_pulse",
        "grape_fock1i3_pulse",
        "grape_fock14_pulse",
        "grape_fock1i4_pulse",
        "grape_fock15_pulse",
        "grape_fock1i5_pulse",
        "grape_fock23_pulse",
        "grape_fock2i3_pulse",
        "grape_fock24_pulse",
        "grape_fock2i4_pulse",
        "grape_fock25_pulse",
        "grape_fock2i5_pulse",
        "grape_fock34_pulse",
        "grape_fock3i4_pulse",
        "grape_fock35_pulse",
        "grape_fock3i5_pulse",
        "grape_fock45_pulse",
        "grape_fock4i5_pulse",
        "coh1",
    ]

    for pulse in pulselist:
        parameters = {
            "modes": ["QUBIT", "CAV", "RR"],
            "reps": 500,
            "wait_time": 16e6,
            "x_sweep": [1, 2, 3, 4, 5],  # only measuring p5 for D6
            "qubit_op": "qubit_gaussian_sig250ns_pi_pulse",
            "cav_op": "coherent_1_long",
            "cav_amp": 0,
            # "plot_quad": "I_AVG",
            "fit_fn": None,
            "single_shot": True,
            "fetch_period": 2,
            "qubit_grape": pulse,
            "cav_grape": pulse,
        }

        plot_parameters = {
            "xlabel": "Measurement times",
            "plot_err": None,
        }

        experiment = NSplitSpectroscopy(**parameters)
        experiment.name = "grapeD6_checkqubit_Pe_" + pulse

        experiment.setup_plot(**plot_parameters)
        prof.run(experiment)
