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
    name = "grape_metrology_check_g"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, cav_grape, qubit_grape, fit_fn, **other_params):
        self.qubit_op = qubit_op
        self.cav_grape = cav_grape
        self.qubit_grape = qubit_grape
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq)
        qubit.play(self.qubit_grape, ampx=1)
        cav.play(self.cav_grape, ampx=1)

        qua.align(cav.name, qubit.name)  # align modes

        # qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes

        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.4
    x_stop = 1.4
    x_step = 0.02

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 500,
        "wait_time": 10e6,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        # "x_sweep": [0, 1, 2, 3, 4, 5],
        # "y_sweep": [0, 1],
        "qubit_op": "qubit_gaussian_short_pi_pulse",
        "single_shot": True,
        # "plot_quad": "I_AVG",
        "fetch_period": 4,
        "qubit_grape": "0+alpha2_700",
        "cav_grape": "0+alpha2_700",
        "fit_fn": "sine",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "plot_err": None,
    }

    experiment = NSplitSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
