"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Wigner2D(Experiment):

    name = "wigner_2d"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        qubit_op_wigner,
        cav_op,
        cav_op_wigner,
        delay,
        fit_fn=None,
        **other_params,
    ):
        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.cav_op_wigner = cav_op_wigner
        self.qubit_op_wigner = qubit_op_wigner
        self.fit_fn = fit_fn
        self.delay = delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, cav, flux = self.modes  # get the modes

        qua.reset_frame(cav.name)

        ##################################################################
        #################### Wigner for vacuum, phase = 0.0 ##############
        ##################################################################

        qua.reset_frame(cav.name)

        # Wigner
        cav.play(
            self.cav_op_wigner,
            ampx=(-self.y, self.x, -self.x, -self.y),
            phase=0.5,
        )
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1)
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1, phase=0.0)

        # Measure qubit state
        qua.align(qubit.name, rr.name, "QUBIT_EF")  # align measurement
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

        ##################################################################
        #################### Wigner for vacuum, phase = 0.5 ##############
        ##################################################################

        qua.reset_frame(cav.name)

        # Wigner
        cav.play(
            self.cav_op_wigner,
            ampx=(-self.y, self.x, -self.x, -self.y),
            phase=0.5,
        )
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1)
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1, phase=0.5)

        # Measure qubit state
        qua.align(qubit.name, rr.name, "QUBIT_EF")  # align measurement
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

        ##################################################################
        #################### Wigner for Fock 1, phase = 0.0 ##############
        ##################################################################

        qua.reset_frame(cav.name)

        # Fock satae preparation
        qubit.play("gaussian_pi")
        qua.align(qubit.name, flux.name)
        flux.play(f"constcos6ns_reset_1to2_27ns_E2pF2pG2pH2", ampx=0.14)
        qua.align()

        # Wigner
        cav.play(
            self.cav_op_wigner,
            ampx=(-self.y, self.x, -self.x, -self.y),
            phase=0.5,
        )
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1)
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1, phase=0.0)

        # Measure qubit state
        qua.align(qubit.name, rr.name, "QUBIT_EF")  # align measurement
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

        ##################################################################
        #################### Wigner for Fock 1, phase = 0.5 ##############
        ##################################################################

        qua.reset_frame(cav.name)

        # Fock satae preparation
        qubit.play("gaussian_pi")
        qua.align(qubit.name, flux.name)
        flux.play(f"constcos6ns_reset_1to2_27ns_E2pF2pG2pH2", ampx=0.14)
        qua.align()

        # Wigner
        cav.play(
            self.cav_op_wigner,
            ampx=(-self.y, self.x, -self.x, -self.y),
            phase=0.5,
        )
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1)
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1, phase=0.5)

        # Measure qubit state
        qua.align(qubit.name, rr.name, "QUBIT_EF")  # align measurement
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

        ##################################################################
        #################### Wigner for Fock 2, phase = 0.0 ##############
        ##################################################################

        qua.reset_frame(cav.name)

        # Fock satae preparation
        qubit.play("gaussian_pi")
        qua.align(qubit.name, flux.name)
        flux.play(f"constcos6ns_reset_1to2_27ns_E2pF2pG2pH2", ampx=0.14)
        qua.align()
        # Fock satae 2 preparation
        qubit.play("gaussian_pi")
        qua.align(qubit.name, flux.name)
        flux.play(f"constcos2ns_reset_1to2_23ns_E2pF2pG2pH2", ampx=0.25)
        qua.align()

        # Wigner
        cav.play(
            self.cav_op_wigner,
            ampx=(-self.y, self.x, -self.x, -self.y),
            phase=0.5,
        )
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1)
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1, phase=0.0)

        # Measure qubit state
        qua.align(qubit.name, rr.name, "QUBIT_EF")  # align measurement
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

        ##################################################################
        #################### Wigner for Fock 2, phase = 0.5 ##############
        ##################################################################

        qua.reset_frame(cav.name)

        # Fock satae preparation
        qubit.play("gaussian_pi")
        qua.align(qubit.name, flux.name)
        flux.play(f"constcos6ns_reset_1to2_27ns_E2pF2pG2pH2", ampx=0.14)
        qua.align()
        # Fock satae 2 preparation
        qubit.play("gaussian_pi")
        qua.align(qubit.name, flux.name)
        flux.play(f"constcos2ns_reset_1to2_23ns_E2pF2pG2pH2", ampx=0.25)
        qua.align()
        
        # Wigner
        cav.play(
            self.cav_op_wigner,
            ampx=(-self.y, self.x, -self.x, -self.y),
            phase=0.5,
        )
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1)
        qua.wait(int(self.delay // 4), cav.name, qubit.name)
        qubit.play(self.qubit_op_wigner, ampx=1, phase=0.5)

        # Measure qubit state
        qua.align(qubit.name, rr.name, "QUBIT_EF")  # align measurement
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.9
    x_stop = 1.91
    x_step = 0.1

    y_start = -1.9
    y_stop = 1.91
    y_step = 0.1

    parameters = {
        "modes": ["QUBIT", "RR", "CAVITY", "FLUX"],
        "reps": 750,
        "wait_time": 0.8e6,  # ns
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "_",
        "cav_op": "_",
        "qubit_op_wigner": "gaussian_pi2_short",
        "cav_op_wigner": "cohstate_1",
        "plot_quad": "I_AVG",
        # "single_shot": False,
        # "fit_fn": "gaussian",
        "delay": 74 * 4,
        "fetch_period": 30,
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": None,
        "skip_plot": True,
    }

    experiment = Wigner2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
