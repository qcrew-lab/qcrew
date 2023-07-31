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

        qua.update_frequency(qubit.name, 60e6)
        qubit.play(self.qubit_grape, ampx=1)
        cav.play(self.cav_grape, ampx=1)

        qua.align(cav.name, qubit.name)  # align modes


        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qubit.play(self.qubit_op, ampx=1)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes

        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 57e6  # -51e6
    x_stop = 61e6  # -49.76e6
    x_step = 0.02e6

    parameters = {
        "modes": ["QUBIT", "CAVB", "RR"],
        "reps": 1000,
        "wait_time": 5000e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "gaussian_pi_pulse_selective",
        "cav_op": "gaussian_coh1",
        "cav_amp": 0,
        "plot_quad": "I_AVG",
        "fetch_period": 5,
        "qubit_grape": "qctrl_fock1_pulse",
        "cav_grape": "qctrl_fock1_pulse",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        # "plot_err" : None,
    }

    experiment = NSplitSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
