"""
A python class describing a cavity displacement calibration using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class CavityDisplacementCal(Experiment):
    name = "RR_displacement_cal"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, rr_drive, qubit_op, fit_fn="displacement_cal", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.rr_drive = rr_drive

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        rr.play(self.rr_drive, duration = 800, ampx=self.x)  # play displacement to cavity
        # qua.align(rr.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align all modes
        qua.wait(int(400))
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4))

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 0
    x_stop = 2.0  # 2.16 # DO NOT CHANGE
    x_step = 0.08

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 500,
        "wait_time": 500e3,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_op": "qubit_gaussian_sel_pi_pulse",

        "rr_drive": "constant_drive",
        # "plot_quad": "I_AVG",
        "single_shot": True,
        "fetch_period": 2,
    }

    plot_parameters = {
        "xlabel": "RR pulse amplitude scaling",
        # "plot_err": None,
    }

    experiment = CavityDisplacementCal(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
