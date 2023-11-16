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
        **other_params,
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

        qua.update_frequency(qubit.name, int(-176.4e6))
        flux.play("constcos20ns_tomo_RO_tomo_E2pF2pG2pH2_11142023", ampx=-0.5662) #-0.5625
        qua.wait(int(900 // 4), qubit.name)
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse

        qua.wait(int(self.rr_delay // 4), rr.name, "QUBIT_EF")  # ns
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    amp_start = -1.9
    amp_stop = 1.91
    amp_step = 0.1
    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 20000,
        "wait_time": 80e3,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "gaussian_pi_short_ecd",
        # "freq_01": int(-48.68e6),
        "qubit_delay": 120,  # ns
        "rr_delay": 1400,  # ns
        "flux_op": "constcos80ns_2000ns_E2pF2pG2pH2", #constcos80ns_tomo_RO_4_E2pF2pG2pH2
        "flux_amp": -0.0696,
        "single_shot": True,
        # "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
    }

    experiment = PowerRabi_FF(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
