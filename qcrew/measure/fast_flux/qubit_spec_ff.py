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
        qubit, rr, flux = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        if 0:  # castle
            flux.play(self.flux_op, duration=99, ampx=self.y)  # to make off resonance
            qua.wait(int((120) // 4), rr.name, qubit.name)  # ns
            qubit.play(self.qubit_op)  # play pi qubit pulse -109e6
            flux.play(self.flux_op, duration=99, ampx=0)  # to make on resonance
            qua.align(flux.name, rr.name)
            flux.play(self.flux_op, duration=1500, ampx=self.y)  # to make off resonance
            qua.wait(int((120) // 4), rr.name)

        if 0:
            qubit.play(self.qubit_op)  # play pi qubit pulse
            qua.align(qubit.name, flux.name)  # wait qubit pulse to end
            flux.play(self.flux_op, duration=16, ampx=-0.25)  #
            qua.align(qubit.name, flux.name)  # wait qubit pulse to end
            qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
            qubit.play(self.qubit_op)
            qua.align(qubit.name, rr.name)  # wait for partial qubit decay

        if 0:
            flux.play(self.flux_op, duration=99, ampx=self.y)  # length 369na self.y
            qua.wait(int(self.qubit_delay // 4), qubit.name)
            qubit.play(self.qubit_op)  # play qubit pulse
            qua.wait(int(self.rr_delay // 4), rr.name)  # wait flux pulse to end
        if 0:  # predistorted pulse
            flux.play(
                f"IIR_square_0726_on_time_196", ampx=self.y
            )  # to make off resonance
            qua.wait(int(self.qubit_delay // 4), qubit.name)
            qubit.play(self.qubit_op)  # play pi qubit pulse
            qua.wait(int((380 + 4) // 4), rr.name)
        if 1:  # castle predistorted
            flux.play(
                "castle_IIR_230727_396ns_0dot00_2250", ampx=self.y
            )  # to make off resonance
            qua.wait(int((250) // 4), rr.name, qubit.name)  # ns
            qubit.play(self.qubit_op)  # play pi qubit pulse -109e6
            qua.wait(int((920) // 4), rr.name)
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
    x_start = -125e6  # -100e6
    x_stop = -55e6  # -40e6
    x_step = 0.75e6

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 100000,
        "wait_time": 60e3, #ns
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": [
            0.574, 0.5,0.4,  0
        ],
        "qubit_op": "gaussian_pi",
        "qubit_delay": 200,  # ns
        "rr_delay": 700,  # ns
        "flux_op": "constant_pulse",
        "fit_fn": "gaussian",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        "fetch_period": 2,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = QubitSpectroscopyFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
