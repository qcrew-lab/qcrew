"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class TOFCalibration(Experiment):

    name = "tof_calibration"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "grape_qubit_op",
        "grape_cav_op",
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "detuning", # Detuning of qubit frequency due to cavity
    }

    def __init__(self, qubit_op, grape_cav_op, grape_qubit_op, fit_fn=None, detuning = 0, **other_params):

        self.qubit_op = qubit_op
        self.grape_cav_op = grape_cav_op
        self.grape_qubit_op = grape_qubit_op
        self.fit_fn = fit_fn

        self.detuning = detuning

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        As a loop, sweep the delay time
            1. Play the optimal state preparation
            2. Play a qubit selective pulse at where it should be
            3. Readout
        """
        qubit, cav, rr, cav_drive, rr_drive = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.detuning)  # update qubit pulse frequency for actual pulse
        
        # Optimal State Preparation pulses
        cav.play(self.grape_cav_op,) 
        qubit.play(self.grape_qubit_op,) 
        
        qua.align(cav.name, qubit.name)  # align modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes

        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.align(cav.name, qubit.name, rr.name, cav_drive.name, rr_drive.name)

        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    delay_start = -200
    delay_stop = 200
    delay_step = 20

    parameters = {
        "modes": ["QUBIT", "CAV", "RR", "CAV_DRIVE", "RR_DRIVE"],
        "reps": 10000,
        "wait_time": 1500000,
        "detuning" : -38.8e6,
        "x_sweep": (int(delay_start), int(delay_stop + delay_step / 2), int(delay_step)),
        "qubit_op": "gaussian_pi_selective_pulse3",
        "grape_cav_op": "cavity_numerical_pulse",
        "grape_qubit_op": "qubit_numerical_pulse",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = TOFCalibration(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
