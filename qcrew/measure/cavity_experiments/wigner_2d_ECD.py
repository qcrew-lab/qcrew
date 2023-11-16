"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
from qcrew.measure.qua_macros import *

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

        # Tune system to ECD point
        qua.update_frequency(cav.name, int(-39.185e6))
        qua.update_frequency(qubit.name, int(-176.4e6))
        qua.align()
        flux.play("constcos80ns_1000ns_E2pF2pG2pH2", ampx=-0.0565)
        qua.wait(int(120 // 4), cav.name, qubit.name)

        # Use ECD to prepare cavity superposition
        # Char_1D_singledisplacement(
        #     cav,
        #     qubit,
        #     "ecd1_displacement",
        #     "gaussian_pi_short_ecd",
        #     "gaussian_pi2_short_ecd",
        #     ampx=0.2,
        #     delay=156,
        #     measure_real=True,
        #     tomo_phase=0,
        #     ampy=0.0,
        # )
        qua.wait(int((640 + 500) // 4), cav.name)

        # Wigner
        qua.update_frequency(cav.name, int(-38.26e6))
        qua.update_frequency(qubit.name, int(-65.16e6))
        cav.play(
            "cohstate_1_short",
            ampx=(-self.y, self.x, -self.x, -self.y),
            phase=0.5,  # 0.25
        )
        qua.align(cav.name, qubit.name)
        # qua.update_frequency(qubit.name, int(-86.6e6))
        qubit.play("gaussian_pi2_short", ampx=1)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4),
            cav.name,
            qubit.name,
        )  # conditional phase gate on even, odd Fock state
        qubit.play("gaussian_pi2_short", ampx=1, phase=0.0)  # play pi/2 pulse around X

        # Measure qubit state
        qua.align(qubit.name, rr.name, "QUBIT_EF")  # align measurement
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state

        # wait system reset
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

    y_start = -1.9
    y_stop = 1.91
    y_step = 0.1

    parameters = {
        "modes": ["QUBIT", "RR", "CAVITY", "FLUX"],
        "reps": 2000,
        "wait_time": 0.5e6,  # ns
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (0.,),  # (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "_",
        "cav_op": "_",
        "qubit_op_wigner": "_",
        "cav_op_wigner": "_",
        # "plot_quad": "I_AVG",
        "single_shot": True,
        "fit_fn": "gaussian",
        "delay": 74 * 4,
        "fetch_period": 30,
    }

    plot_parameters = {
        "xlabel": "X",
        # "ylabel": "Y",
        # "plot_type": "2D",
        # "cmap": "bwr",
        # "plot_err": None,
        # "skip_plot": True,
    }

    experiment = Wigner2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
