"""
A python class describing a cavity T1 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Cavity_Qswitch(Experiment):
    name = "cavity_qswitch"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn=None, **other_params):
        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, cav_drive, rr_drive = self.modes  # get the modes

        cav.play(self.cav_op, ampx=1)  # play displacement to cavity

        qua.update_frequency(rr_drive.name, self.x)  # update resonator pulse frequency
        qua.wait(int(8), cav.name, qubit.name, rr.name, cav_drive.name, rr_drive.name)
        qua.align()
        rr_drive.play("res_drive", duration=self.y, ampx=1.5)
        cav_drive.play("cav_drive", duration=self.y, ampx=1)
        qua.align()
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align()
        rr.measure((self.I, self.Q))  # measure transmitted signal

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        qua.wait(
            int(self.wait_time // 4), cav.name, qubit.name, rr.name
        )  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    drive_freq_start = 43.1e6
    drive_freq_stop = 47.1e6
    drive_freq_step = 0.05e6
    plen_start = 150e3
    plen_stop = 300e3  # clock cycles
    plen_step = 5e3

    parameters = {
        "modes": ["QUBIT", "CAV", "RR", "CAV_DRIVE", "RR_DRIVE"],
        "reps": 1000,
        "wait_time": 10e6,
        "x_sweep": (
            int(drive_freq_start),
            int(drive_freq_stop + drive_freq_step / 2),
            int(drive_freq_step),
        ),
        "y_sweep": (
            int(plen_start),
            int(plen_stop + plen_step / 2),
            int(plen_step),
        ),
        # "x_sweep": (int(plen_start), int(plen_stop + plen_step / 2), int(plen_step)),
        "qubit_op": "qubit_gaussian_sel_pi_pulse",
        "cav_op": "coherent_1_long",
        "single_shot": False,
        "fetch_period": 4,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "ylabel": "drive duration",
        "xlabel": "drive frequency",
        "plot_type": "2D",
        "plot_err": False,
    }

    experiment = Cavity_Qswitch(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
