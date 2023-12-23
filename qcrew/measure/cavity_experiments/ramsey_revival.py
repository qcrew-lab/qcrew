"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Ramseyrevival(Experiment):

    name = "ramsey_revival"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, rr_delay, qubit_delay, cav_op, fit_fn=None, **other_params
    ):

        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.fit_fn = fit_fn
        self.rr_delay = rr_delay
        self.qubit_delay = qubit_delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes
        cav.play(self.cav_op, ampx=3)  # prepare cavity state
        qua.align(cav.name, qubit.name)  # align modes
        qubit.play(self.qubit_op, ampx=1)  # play qubit pulse
        qua.wait(self.x, qubit.name)
        qubit.play(self.qubit_op, ampx=1)  # play  qubit pulse with pi/2
        qua.align()
        if 0:
            flux.play("constcos20ns_tomo_RO_tomo_new_E2pF2pG2pH2_3", ampx=-0.5705)  # lk
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.1)  # rr
        if 1:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0526)  # hk

        # Preselection
        qua.wait(int(30 // 4), rr.name, "QUBIT_EF")  # ns
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 1
    x_stop = 350
    x_step = 2

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 10000,
        "wait_time": 1e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "gaussian_pi2_short",
        "cav_op": "gaussian_cohstate_1_hk",
        # "single_shot": True,
        "fetch_period": 5,
        "plot_quad": "I_AVG",
        "qubit_delay": 120,  # ns
        "rr_delay": 520,  # ns
        "fit_fn": "gaussian",
    }

    plot_parameters = {
        "xlabel": "Wait time (clock)",
    }

    experiment = Ramseyrevival(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
