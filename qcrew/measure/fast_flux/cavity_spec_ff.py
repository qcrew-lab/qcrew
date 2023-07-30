"""
A python class describing a cavity spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class CavitySpectroscopyFastFlux(Experiment):

    name = "cavcavity_spec_ffity_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn="gaussian", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes

        # Fock satae preparation
        flux.play("predist_constcos_reset_pulse", ampx=self.y)
        qua.update_frequency(cav.name, self.x)  # update resonator pulse frequency
        qua.align(cav.name, flux.name)
        qua.wait(int(1700 // 4), cav.name)
        cav.play(self.cav_op)  # play displacement to cavity
        qua.align(cav.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align all modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------


if __name__ == "__main__":

    x_start = -60e6
    x_stop = -30e6
    x_step = 0.25e6
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 50000,
        "wait_time": 700e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (0.0, -0.295),
        "qubit_op": "constant_pi",
        "fetch_period": 3,
        "single_shot": True,
        "cav_op": "const_cohstate_1",
    }

    plot_parameters = {
        "xlabel": "Cavity pulse frequency (Hz)",
    }

    experiment = CavitySpectroscopyFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
