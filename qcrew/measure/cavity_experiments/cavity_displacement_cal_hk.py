"""
A python class describing a cavity displacement calibration using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class CavityDisplacementCal(Experiment):

    name = "cavity_displacement_cal"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, qubit_op, fit_fn="quadratic", **other_params):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes
        # qua.reset_frame(cav.name)
        # qua.reset_frame(qubit.name)
        
        # qua.update_frequency(cav.name, int(-38.67e6), keep_phase=True)
        # qua.update_frequency(qubit.name, int(-93.19e6), keep_phase=True)
        cav.play(self.cav_op, ampx=self.x)  # play displacement to cavity
        # cav.play(self.cav_op, ampx=self.x)  # play displacement to cavity
        # cav.play(self.cav_op, ampx=self.x)  # play displacement to cavity
        # cav.play(self.cav_op, ampx=self.x)  # play displacement to cavity
        # cav.play(self.cav_op, ampx=self.x)  # play displacement to cavity
        qua.align(cav.name, qubit.name)  # align all modes
        qubit.play(self.qubit_op)  # play qubit pulse

        # qua.align()  # wait qubit pulse to end
        qua.align()
        if 0:
            flux.play("constcos20ns_tomo_RO_tomo_new_E2pF2pG2pH2_3", ampx=-0.5685)  # lk
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.1)  # rr
        if 0:
            flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0527)  # hk
        # qua.wait(int(30 // 4), rr.name, "QUBIT_EF")  # ns
        # qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure qubit state

        # rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()
        qua.align()


# stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 0.0
    x_stop = 1.25
    x_step = 0.1
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 300000,
        "wait_time": 1e6,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        # "y_sweep": [-0.4, 0.0, 0.4],
        "qubit_op": "gaussian_pi_hk_160",
        "cav_op": "cohstate_2dot5_short_hk",
        # "fetch_period": 20,
        # "single_shot": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Cavity pulse amplitude scaling",
    }

    experiment = CavityDisplacementCal(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
