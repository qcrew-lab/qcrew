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
class CohErrPND(Experiment):
    name = "PND_CoherentError"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, cav_op, cav_grape, qubit_grape, fit_fn=None, **other_params
    ):
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.cav_grape = cav_grape
        self.qubit_grape = qubit_grape
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.update_frequency(qubit.name, qubit.int_freq)

        # the 1st selection
        rr.measure((self.I, self.Q))
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        qua.align()
        qua.wait(250)
        qua.align()
        # the 1st selection

        if self.cav_grape == "vacuum":
            pass
        elif self.cav_grape == "coh1":
            cav.play(self.cav_op, ampx=(1, 0, 0, 1), phase=-0.25)
        else:
            qubit.play(self.qubit_grape)
            cav.play(self.cav_grape)

        qua.align()
        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse

        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    pulses = [
        "vacuum",
        "grape_fock1",
        "grape_fock2",
        "grape_fock3",
        "grape_fock4",
        "grape_fock5",
    ]

    x0_center = -60.00e6
    x1_center = -61.35e6
    x2_center = -62.72e6
    x3_center = -64.08e6
    x4_center = -65.47e6
    x5_center = -66.86e6
    # x6_center = e6
    # x7_center = e6

    chi = 1.359e6
    bw = 0.0e6  # will do the same point 5 times
    points = 5

    x0 = np.linspace(x0_center - bw, x0_center + bw, points)
    x1 = np.linspace(x1_center - bw, x1_center + bw, points)
    x2 = np.linspace(x2_center - bw, x2_center + bw, points)
    x3 = np.linspace(x3_center - bw, x3_center + bw, points)
    x4 = np.linspace(x4_center - bw, x4_center + bw, points)
    x5 = np.linspace(x5_center - bw, x5_center + bw, points)

    sweeps = np.array([x0, x1, x2, x3, x4, x5], dtype="int").tolist()

    # xlist = np.array(x5, dtype="int").tolist()  # only p5

    for i, pulse in enumerate(pulses):
        parameters = {
            "modes": ["QUBIT", "CAV", "RR"],
            "reps": 200,
            "wait_time": 16e6,
            "x_sweep": sweeps[i],  # only measuring p5 for D6
            "qubit_op": "qubit_gaussian_sig250ns_pi_pulse",
            "cav_op": "coherent_1_long",
            # "plot_quad": "I_AVG",
            "fit_fn": None,
            "single_shot": True,
            "fetch_period": 4,
            "qubit_grape": pulse,
            "cav_grape": pulse,
        }

        plot_parameters = {
            "xlabel": "Qubit pulse frequency (Hz)",
            "plot_err": None,
        }

        experiment = CohErrPND(**parameters)
        experiment.name = "Coherent_Error_PND_" + str(pulse)

        experiment.setup_plot(**plot_parameters)
        prof.run(experiment)
