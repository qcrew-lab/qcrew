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
class parityDecay(Experiment):
    name = "parity_decay"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",
    }

    def __init__(
        self,
        qubit_op,
        cav_grape,
        qubit_grape,
        delay,
        qubit_freq,
        fit_fn=None,
        **other_params
    ):
        self.qubit_op = qubit_op
        self.cav_grape = cav_grape
        self.qubit_grape = qubit_grape
        self.fit_fn = fit_fn
        self.delay = delay
        self.qubit_freq = qubit_freq

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq)
        if self.cav_grape == "vacuum":
            pass
        else:
            qubit.play(self.qubit_grape)
            cav.play(self.cav_grape)
        qua.align()
        # qua.update_frequency(qubit.name, 176.05e6)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        # conditional phase gate on even, odd Fock state
        # qua.update_frequency(qubit.name, 176.05e6)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    pulselist = [
        # "vacuum",
        # "grape_fock1_pulse",
        # "grape_fock2_pulse",
        # "grape_fock3_pulse",
        # "grape_fock4_pulse",
        # "grape_fock5_pulse",
        # "grape_fock6_pulse",
        "grape_fock8_pulse",
    ]

    qubit_freqs = np.array(
        [
            177.406e6,
            176.05e6,
            174.69e6,
            173.325e6,
            171.915e6,
            170.535e6,
            169.135e6,
            167.7e6,
        ],
        dtype="int",
    ).tolist()

    for i, pulse in enumerate(pulselist):
        parameters = {
            "modes": ["QUBIT", "CAV", "RR"],
            "reps": 1000,
            "wait_time": 10e6,
            "delay": 289,
            "x_sweep": [0, 1, 2, 3, 4],
            "qubit_op": "qubit_gaussian_short_pi2_pulse",
            "qubit_freq": qubit_freqs[i],
            "qubit_grape": pulse,
            "cav_grape": pulse,
            # "plot_quad": "I_AVG",
            "single_shot": True,
            "fetch_period": 2,
        }

        plot_parameters = {"xlabel": "Qubit pulse frequency (Hz)", "plot_err": None}
        experiment = parityDecay(**parameters)
        experiment.name = (
            "QML_number_split_spec_"
            + pulse
            # + "_point{}".format(i + 1)
            # "QML_number_split_spec_" + pulse + "_no_displacement"
        )

        experiment.setup_plot(**plot_parameters)
        prof.run(experiment)
