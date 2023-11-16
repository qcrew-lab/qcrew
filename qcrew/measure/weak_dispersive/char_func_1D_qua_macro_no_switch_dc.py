from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class CharacteristicFunction1D(Experiment):

    name = "characteristic_function_1D_dc"
    # just dc
    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_state_op",
        "char_func_displacement",  # operation for displacing the cavity
        "qubit_pi",
        "qubit_pi2",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
        "measure_real",
    }

    def __init__(
        self,
        cav_state_op,
        char_func_displacement,
        qubit_pi,
        qubit_pi2,
        fit_fn="gaussian",
        delay=4,
        measure_real=True,
        **other_params,
    ):
        self.cav_state_op = cav_state_op
        self.char_func_displacement = char_func_displacement
        self.qubit_pi = qubit_pi
        self.qubit_pi2 = qubit_pi2
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr, flux = self.modes  # get the modes
        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)

        # flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=-0.258)
        # qua.wait(int(200 // 4), cav.name, qubit.name)  # ns
        Char_2D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            0,
            self.x,
            delay=self.delay,
            measure_real=self.measure_real,
            tomo_phase=0.0,
            correction_phase=0,
        )

        # Measure cavity state
        qua.align(rr.name, "QUBIT_EF", qubit.name)
        # qua.wait(int(100 // 4), rr.name, "QUBIT_EF")  # ns
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        # wait system reset


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.90
    x_stop = 1.91
    x_step = 0.1

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 20000,
        "wait_time": 1e6,
        "fetch_period": 5,  # time between data fetching rounds in sec
        "delay": 116,  # 188,  # wait time between opposite sign displacements
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        # "y_sweep": (0, 1),
        "qubit_pi": "gaussian_pi_short_ecd",
        "qubit_pi2": "gaussian_pi2_short_ecd",
        "char_func_displacement": "ecd2_displacement",
        "cav_state_op": "_",
        "fit_fn": "gaussian",
        "measure_real": True,
        "single_shot": True,
        # "plot_quad": "I_AVG",  # measure real part of char function if True, imag Part if false
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        # "ylabel": "Y",
        # "plot_type": "2D",
        "cmap": "bwr",
    }

    experiment = CharacteristicFunction1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
