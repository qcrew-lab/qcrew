"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class PowerRabi_FF(Experiment):

    name = "power_rabi_ff"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        # freq_01,
        flux_amp,
        flux_op,
        qubit_op,
        qubit_delay,
        rr_delay,
        fit_fn="sine",
        **other_params
    ):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.qubit_delay = qubit_delay
        self.rr_delay = rr_delay
        # self.freq_01 = freq_01
        self.flux_amp = flux_amp
        self.flux_op = flux_op

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes

        if 1:
            flux.play("square_IIR_long", ampx=0.625)
            qua.wait(int((20) // 4), qubit.name)
            qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
            qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
            # qua.align()
            
            ##readout pulse
            # qua.align()  # align measurement
            # flux.play("detuned_readout", ampx=-0.5)
            qua.wait(100, rr.name)
        if 0:
            flux.play(
                "castle_IIR_230727_300ns_0dot00", ampx=0.49
            )  # to make off resonance
            qua.wait(int((450) // 4), rr.name, qubit.name)  # ns
            qubit.play(self.qubit_op, ampx=self.x)  # play pi qubit pulse -109e6
            qua.wait(int((920) // 4), rr.name)

        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1.2
    amp_stop = 1.2
    amp_step = 0.05
    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 100000,
        "wait_time": 60e3,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "gaussian_pi",
        # "freq_01": int(-48.68e6),
        "qubit_delay": 400,  # ns
        "rr_delay": 2500 + 900,  # ns
        "flux_op": "square_IIR_superf_readout",
        "flux_amp": -0.5,
        # "single_shot": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
    }

    experiment = PowerRabi_FF(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
