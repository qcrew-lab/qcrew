from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *


# ---------------------------------- Class -------------------------------------


class CharacteristicFunction2D(Experiment):

    name = "characteristic_function_2D"

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
        fit_fn=None,
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

        # Coherent state preparation and evolution
        qua.update_frequency(cav.name, int(-39.09e6), keep_phase=True)
        qua.update_frequency(qubit.name, int(-226.3e6), keep_phase=True)
        cav.play("cohstate_5_short", ampx=1)
        qua.align(cav.name, qubit.name)
        qubit.play("gaussian_pi", ampx=1)
        qua.wait(200, qubit.name)
        qubit.play("gaussian_pi", ampx=1)
        qua.wait(200, qubit.name)
        qubit.play("gaussian_pi", ampx=1)
        qua.wait(200, qubit.name)
        qubit.play("gaussian_pi", ampx=1)
        qua.wait(200, qubit.name)
        qubit.play("gaussian_pi", ampx=1)
        qua.wait(200, qubit.name)
        qua.update_frequency(cav.name, cav.int_freq)
        qua.update_frequency(qubit.name, qubit.int_freq)
        qua.wait(1250 * 2, cav.name)
        qua.align()

        # Bias qubit to ECD point
        # flux.play("constcos80ns_tomo_RO_3_E2pF2pG2pH2", ampx=0.03645)
        # qua.wait(25, cav.name, qubit.name)

        # Bias qubit to ECD point
        flux.play("constcos20ns_tomo_RO_tomo_2_E2pF2pG2pH2", ampx=-0.121)

        # Preselection
        qua.wait(int(30 // 4), rr.name, "QUBIT_EF")  # ns
        qua.play("digital_pulse" * qua.amp(1.0), "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure transmitted signal=

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.wait(int((60 + 850) // 4), cav.name, qubit.name)

        ######################  Measure the created state with charactristic function  #####################
        # this uses ampx matrixes. this somehow makes all pulses smaller by approx fac. sqrt2
        Char_2D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            self.x,
            self.y,
            delay=self.delay,
            measure_real=self.measure_real,
            tomo_phase=0,
            correction_phase=-0.0111 - 0.5424,
        )  # 0.0372- 0.2312 - 0.2107,

        # Measure qubit state
        qua.align(rr.name, "QUBIT_EF", qubit.name)
        qua.wait(int(20 // 4), rr.name, "QUBIT_EF")  # ns
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
    x_start = -1.90
    x_stop = 1.91
    x_step = 0.1

    y_start = -1.9
    y_stop = 1.91
    y_step = 0.1

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
        "reps": 10000,
        "wait_time": 0.3e6,
        "fetch_period": 60,  # time between data fetching rounds in sec
        "delay": 116,  # wait time between opposite sign displacements
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_pi": "gaussian_pi_short_ecd",
        "qubit_pi2": "gaussian_pi2_short_ecd",
        "char_func_displacement": "ecd2_displacement",
        "cav_state_op": "_",
        "measure_real": True,
        "single_shot": True,
        # "plot_quad": "I_AVG",  # measure real part of char function if True, imag Part if false
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "skip_plot": True,
    }

    experiment = CharacteristicFunction2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
