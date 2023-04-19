"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class NSplitSpectroscopy(Experiment):

    name = "number_split_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        cav_op,
        cav_amp,
        cav_grape,
        qubit_grape,
        fit_fn=None,
        **other_params
    ):

        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.cav_amp = cav_amp
        self.cav_grape = cav_grape
        self.qubit_grape = qubit_grape
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, 60e6)
        qubit.play(
            self.qubit_grape, ampx=1,
        )
        cav.play(
            self.cav_grape, ampx=self.y,
        )

        qua.align(cav.name, qubit.name)  # align modes

        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes

        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 58e6  # -51e6
    x_stop = 60.5e6  # -49.76e6
    x_step = 0.02e6

    y_start = 0.9  # -51e6
    y_stop = 1.1  # -49.76e6
    y_step = 0.04

    parameters = {
        "modes": ["QUBIT", "CAVB", "RR"],
        "reps": 200,
        "wait_time": 2000e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "constant_pi_selective_pulse2",
        "plot_quad": "I_AVG",
        "fetch_period": 10,
        "qubit_grape": "grape_fock02_thermal_pulse",
        "cav_grape": "grape_fock02_thermal_pulse",
        "cav_op": None,
        "cav_amp": None,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "ylabel": "Cavity grape scaling",
        "plot_type": "2D",
    }

    experiment = NSplitSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
