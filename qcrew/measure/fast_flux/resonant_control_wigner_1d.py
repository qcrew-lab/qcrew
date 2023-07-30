"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class ResonantCtrlFastFluxWigner1D(Experiment):

    name = "resonant_ctrl_wigner_1d"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        qubit_op_wigner,
        cav_op,
        delay,
        pi_01m,
        fit_fn=None,
        **other_params
    ):

        self.pi_01m = pi_01m
        self.qubit_op = qubit_op
        self.qubit_op_wigner = qubit_op_wigner
        self.cav_op = cav_op
        self.fit_fn = fit_fn
        self.delay = delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux, cav = self.modes  # get the modes

        qua.reset_frame(cav.name)

        # Fock satay preparation
        flux.play("pd_sq_2us_on_2us_hold_pulse", ampx=-0.36)
        qua.wait(int(150 // 4), qubit.name)
        qua.update_frequency(qubit.name, int(-50.07e6))
        qubit.play(self.pi_01m, ampx=self.y)  # play pi pulse to (g,0)->(1,-)

        # Wigner
        # qua.align(cav.name, flux.name)
        qua.wait(int(2000 // 4), cav.name)
        # cav.play(self.cav_op, ampx=self.x, phase=0)  # displacement in I direction
        cav.play(
            self.cav_op,
            ampx=(self.x, -self.y, self.y, self.x),
            phase=0.0,
        )
        qua.align(cav.name, qubit.name)
        qua.update_frequency(qubit.name, int(-93.56e6))
        qubit.play(self.qubit_op, ampx=1.0)  # play pi/2 pulse around X
        qua.wait(int(self.delay // 4), qubit.name)
        qua.update_frequency(qubit.name, int(-93.56e6))
        qubit.play(self.qubit_op, ampx=1.0)  # play pi/2 pulse around X

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4))

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.9
    x_stop = 1.9
    x_step = 0.05

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX", "CAVITY"],
        "reps": 10000,
        "wait_time": int(700e3),
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (0.0, 1.0),  # x_start, x_stop + x_step / 2, x_step),
        # "y_sweep": (0.0, 1.0),
        "qubit_op": "gaussian_pi2",
        "qubit_op_wigner": "gaussian_pi2",
        "pi_01m": "gaussian_sel_pi_01p",
        "cav_op": "const_cohstate_1",
        # "plot_quad": "I_AVG",
        "fit_fn": "gaussian",
        "delay": 180,  # pi/chi
        "fetch_period": 10,
        "single_shot": True,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        # "plot_type": "2D",
        "cmap": "bwr",
    }

    experiment = ResonantCtrlFastFluxWigner1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
