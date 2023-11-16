"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Wigner1D(Experiment):

    name = "wigner_1d"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        cav_op,
        qubit_op,
        qubit_op_wigner,
        cav_op_wigner,
        delay,
        cut,
        fit_fn="gaussian",
        **other_params,
    ):

        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.qubit_op_wigner = qubit_op_wigner
        self.cav_op_wigner = cav_op_wigner
        self.fit_fn = fit_fn
        self.delay = delay
        self.cut = cut

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, cav, flux = self.modes  # get the modes

        qua.reset_frame(cav.name)

        # Fock satae preparation
        qubit.play("gaussian_pi", ampx=1)
        qua.align(qubit.name, flux.name)
        flux.play(f"constcos6ns_reset_1to2_28ns_E2pF2pG2pH2", ampx=0.1458)
        qua.align()
        # # Fock satae 2 preparation
        # qubit.play("gaussian_pi")
        # qua.align(qubit.name, flux.name)
        # flux.play(f"constcos2ns_reset_1to2_23ns_E2pF2pG2pH2", ampx=0.25)

        # Wigner 1d
        ## single displacement
        qua.align()
        cav.play(
            self.cav_op_wigner,
            ampx=(-self.cut, self.x, -self.x, -self.cut),
            phase=0.0,
        )
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner)
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, phase=self.y)

        # Measure cavity state
        qua.align(qubit.name, rr.name, "QUBIT_EF")  # align measurement
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state

        # wait system reset
        qua.align()
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.9
    x_stop = 1.91
    x_step = 0.1

    parameters = {
        "modes": ["QUBIT", "RR", "CAVITY", "FLUX"],
        "reps": 10000,
        "wait_time": 1.0e6,  # 700e3 #ns
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (0.0, 0.5),
        "cut": 0.0,
        "qubit_op": "_",
        "cav_op": "_",
        "qubit_op_wigner": "gaussian_pi2_short",
        "cav_op_wigner": "cohstate_1",
        "single_shot": True,
        # "plot_quad": "I_AVG",
        "fit_fn": "gaussian",
        "delay": 74 * 4,  # pi/chi 208 ns 472
        "fetch_period": 5,
    }

    plot_parameters = {
        # "xlabel": "X",
        "ylabel": "Y",
        # "plot_type": "2D",
        # "cmap": "bwr",
        # "plot_err": None,
    }

    experiment = Wigner1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
