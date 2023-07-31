"""
A python class describing a readout resonator spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class RRSpectroscopy(Experiment):

    name = "cav_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn=None, **other_params):

        self.fit_fn = fit_fn
        self.cav_op = cav_op
        self.qubit_op = qubit_op

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (cav, drive_cav, rr, qubit) = self.modes  # get the modes

        
        drive_cav.play("constant_cos_pulse", ampx=self.y)  # Play continuous pump

        qua.wait(int(100 / 4), cav.name)

        qua.update_frequency(cav.name, self.x)  # update resonator pulse frequency
        cav.play(self.cav_op, ampx=1)  # play displacement to cavity
        qua.align()  # align all modes
        qua.wait(int(100 / 4), qubit.name)
        
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align all modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -100.6e6
    x_stop = -98.6e6
    x_step = 0.1e6

    amp_start = 0.0
    amp_stop = 1
    amp_step = 0.1

    parameters = {
        "modes": ["CAVB", "DRIVE_RES", "RR", "QUBIT"],
        "reps": 5000,
        "wait_time": 5000e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "gaussian_pi_pulse_selective",
        "cav_op": "gaussian_coh1_longer",
        "plot_quad": "I_AVG",
        # "cable_delay": 0.5e-6,#5e-6,
        "fit_fn": None,
        "fetch_period": 60,
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
        "ylabel": "Pump amplitude scaling",
        "plot_type": "2D",
    }

    experiment = RRSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
