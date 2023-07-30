"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class ResonantCtrlFastFlux(Experiment):

    name = "resonant_ctrl"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_spec_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_spec_op,
        freq_01m,
        flux_amp,
        flux_op,
        qubit_delay,
        nsplit_delay,
        pi_01m,
        fit_fn=None,
        **other_params
    ):

        self.pi_01m = pi_01m
        self.qubit_spec_op = qubit_spec_op
        self.fit_fn = fit_fn
        self.flux_op = flux_op
        self.freq_01m = freq_01m
        self.flux_amp = flux_amp
        self.qubit_delay = qubit_delay
        self.nsplit_delay = nsplit_delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux, cav = self.modes  # get the modes

        flux.play(self.flux_op, ampx=self.flux_amp)
        qua.wait(int(self.qubit_delay // 4), qubit.name)

        qua.update_frequency(qubit.name, self.freq_01m)
        qubit.play(self.pi_01m, ampx=self.y)  # play pi pulse to (g,0)->(1,-)

        # number split spectroscopy
        qua.wait(int(self.nsplit_delay // 4), qubit.name)
        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qubit.play(self.qubit_spec_op)  # play qubit pi pulse

        # readout
        qua.align(rr.name, qubit.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -125e6
    x_stop = -110e6
    x_step = 0.2e6

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX", "CAVITY"],
        "reps": 100000,
        "wait_time": 700e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (0.0, 1.0),
        "flux_amp": -0.28,
        "flux_op": "predist_square_plusminus_pulse",
        "qubit_spec_op": "constant_pi",
        "freq_01m": int(-48.68e6),
        "qubit_delay": 400,  # ns
        "nsplit_delay": 2000,  # ns
        "pi_01m": "gaussian_pi_long",
        "plot_quad": "I_AVG",
        # "single_shot": True,
        "fit_fn": "gaussian",
        "fetch_period": 10,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = ResonantCtrlFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
