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
        self, qubit_op, cav_op, cav_amp, rr_drive, fit_fn=None, **other_params
    ):
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.rr_drive = rr_drive
        self.cav_amp = cav_amp
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        ring_up_time = 380
        ring_down_time = 320

        # qua.reset_frame(cav.name)
        # qua.update_frequency(qubit.name, qubit.int_freq)
        rr.play(
            self.rr_drive,
            duration=(ring_up_time),
            ampx=self.y,
        )
        qua.wait(self.x)

        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    ring_up_time = 380  # clock cycle
    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 2500,
        "wait_time": 2e6,
        "x_sweep": [4, 500, 16],
        "y_sweep": [0, 1.9, 0.4],  # only measuring p5 for D6
        "qubit_op": "qubit_gaussian_sig250ns_pi_pulse",
        "cav_op": "coherent_1_long",
        "cav_amp": 0,
        "rr_drive": "constant_drive",
        "plot_quad": "I_AVG",
        "fit_fn": None,
        
        # "single_shot": True,
        "fetch_period": 2,
    }

    plot_parameters = {
        "xlabel": "wait time after rr-drive",
        "plot_err": True,
    }

    experiment = NSplitSpectroscopy(**parameters)
    experiment.name = "check_rr_drive_readout_effect"

    experiment.setup_plot(**plot_parameters)
    prof.run(experiment)
