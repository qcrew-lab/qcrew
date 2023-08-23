"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitSpectroscopyFastFlux(Experiment):

    name = "qubit_spec_ff"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, rr_delay, qubit_delay, flux_op, fit_fn=None, **other_params
    ):

        self.flux_op = flux_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.rr_delay = rr_delay
        self.qubit_delay = qubit_delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux, cav = self.modes  # get the modes
        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        cav.play("cohstate_1", ampx=self.y)
        qua.align()
        # flux.play(self.flux_op, ampx=self.y)  # to make off resonance
        flux.play(self.flux_op, ampx=1.85)
        # qua.wait(int((self.qubit_delay) // 4), qubit.name)  # ns
        qua.wait(int((20) // 4), qubit.name)  # ns
        qubit.play(self.qubit_op)  # play pi qubit pulse -109e6
        qua.wait(int((self.rr_delay) // 4), rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

 
# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -61e6
    x_stop = -48e6
    x_step = 0.2e6

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX", "CAVITY"],
        "reps": 100000,
        "wait_time": 1000e3,  # ns
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": [0.0, 1.0],
        "qubit_op": "gaussian_pi_320",
        "qubit_delay": 4,  # ns
        "rr_delay": 2000 + 250,  # ns
        # "flux_op": "square_1500ns_ApBpCpD",
        "flux_op": "square_2000ns_ApBpG",
        "fit_fn": "gaussian",
        # "single_shot": True,
        "plot_quad": "Z_AVG",
        "fetch_period": 20,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = QubitSpectroscopyFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
