"""
A python class describing a cavity spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.control.pulses import gaussian_pulse
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class CavitySpectroscopy(Experiment):

    name = "cavity_spec"

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
        
        qua.update_frequency(cav.name, self.x)  # update resonator pulse frequency
        qubit.play("gaussian_pi_hk", ampx=self.y)
        qua.align()  # align all modes
        cav.play(self.cav_op)  # play displacement to cavity
        qua.align(cav.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align()  # wait qubit pulse to end
        if 0:
            flux.play("constcos20ns_tomo_RO_tomo_new_E2pF2pG2pH2_3", ampx=-0.5685)  # lk
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.1)  # rr
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0526)  # hk
        # qua.wait(int(30 // 4), rr.name, "QUBIT_EF")  # ns
        # qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure qubit state

        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------


if __name__ == "__main__":

    x_start = -45e6
    x_stop = -32e6
    x_step = 0.2e6
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 100000,
        "wait_time": 0.5e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (0.0, 1.0),
        "qubit_op": "gaussian_pi_hk_320",
        "plot_quad": "I_AVG",
        "fetch_period": 10,
        # "single_shot": True,
        # "cav_op": "cohstate_1_long",
        "cav_op": "spectroscopy_pulse",

    }

    plot_parameters = {
        "xlabel": "Cavity pulse frequency (Hz)",
    }

    experiment = CavitySpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
