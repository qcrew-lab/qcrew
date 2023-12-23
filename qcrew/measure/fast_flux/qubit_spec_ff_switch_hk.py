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

    name = "qubit_spec_ff_hk"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, rr_delay, qubit_delay, flux_amp, flux_op, fit_fn=None, **other_params
    ):

        self.flux_op = flux_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.rr_delay = rr_delay
        self.qubit_delay = qubit_delay
        self.flux_amp = flux_amp

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux, cav = self.modes  # get the modes
        # qubit.lo_freq = 5.1937e9
        # qubit.lo_freq = 5.1937e9 + 250e6 + 326.3e6
        qua.update_frequency(qubit.name, self.x)
        with qua.switch_(self.y):
            with qua.case_(0):
                qubit.play(self.qubit_op, ampx=1)  # play qubit pulse
                qua.align()
                qua.wait(50, flux.name)
                flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=self.flux_amp)
            with qua.case_(1):
                flux.play(
                    "constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=self.flux_amp
                )  # -0.5625
                qua.wait(50, qubit.name)
                qubit.play(self.qubit_op, ampx=1)  # rr
            with qua.case_(2):
                flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=self.flux_amp)
                qua.wait(220, qubit.name)
                qubit.play(self.qubit_op, ampx=1)  # char
            with qua.case_(3):
                flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=self.flux_amp)
                qua.wait(370, qubit.name)
                qubit.play(self.qubit_op, ampx=1)  # rr
            with qua.case_(4):
                flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=self.flux_amp)
                qua.wait(int(900 // 4), qubit.name)
                qubit.play("gaussian_pi2_short_ecd", ampx=1)  # play qubit pulse
        # qua.wait(int(100 // 4), qubit.name)u
        # qua.align()
        # flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0524)  # -0.5625
        # qua.wait(50, qubit.name)
        # qua.wait(int(20 // 4), rr.name, "QUBIT_EF")  # ns
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx = 0)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()


# -------------------------------- Execution ------------------8-----------------

if __name__ == "__main__":
    # x_start = -100e6
    # x_stop = -80e6
    # x_step =0.5e6
    x_start = -180e6
    x_stop = -89e6
    x_step = 0.5e6

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX", "CAVITY"],
        "reps": 1000000,
        "wait_time": 80000,  # 0.8e6,  # ns
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        # "y_sweep": [-0.31],
        "y_sweep": (0,1, 2),
        "qubit_op": "gaussian_pi_hk_80",  # constant_pi_short gaussian_pi_80
        "qubit_delay": 200,  # ns
        "rr_delay": 1300,  # 800,  # ns
        "flux_op": "constcos80ns_2000ns_E2pF2pG2pH2",  # constcos10ns_1500ns_E2pF2pG2pH2 constcos80ns_2000ns_E2pF2pG2pH2
        "fit_fn": "gaussian",
        "flux_amp": 0.0527,
        # "single_shot": True,
        "plot_quad": "I_AVG",
        # "fetch_period": 10,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = QubitSpectroscopyFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
