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

        ##################################################################
        #################### Imag Characteristic for alpha1 ##############
        ##################################################################

        # Reboot
        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)
        qua.align()

        # Coherent state preparation
        qua.update_frequency(cav.name, int(-39.09e6), keep_phase=True)
        cav.play("cohstate_1_short", ampx=1)
        qua.update_frequency(cav.name, cav.int_freq)

        # Evolution
        qua.wait(1250 * 2, cav.name)
        qua.align()

        # Bias qubit to ECD point
        flux.play("constcos80ns_tomo_RO_4_E2pF2pG2pH2", ampx=-0.0696)
        qua.wait(25, cav.name, qubit.name)

        # Characteristic function
        Char_2D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            self.x,
            self.y,
            delay=self.delay,
            measure_real=False,
            tomo_phase=-0.16329,
            correction_phase=-0.011106,
        )

        # Measure qubit state
        qua.wait(int(750 // 4), rr.name, "QUBIT_EF")
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

        ##################################################################
        #################### Imag Characteristic for alpha2 ##############
        ##################################################################

        # Reboot
        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)
        qua.align()

        # Coherent state preparation
        qua.update_frequency(cav.name, int(-39.09e6), keep_phase=True)
        cav.play("cohstate_2_short", ampx=1)
        qua.update_frequency(cav.name, cav.int_freq)

        # Evolution
        qua.wait(1250 * 2, cav.name)
        qua.align()

        # Bias qubit to ECD point
        flux.play("constcos80ns_tomo_RO_4_E2pF2pG2pH2", ampx=-0.0696)
        qua.wait(25, cav.name, qubit.name)

        # Characteristic function
        Char_2D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            self.x,
            self.y,
            delay=self.delay,
            measure_real=False,
            tomo_phase=-0.16329,
            correction_phase=-0.011106,
        )

        # Measure qubit state
        qua.wait(int(750 // 4), rr.name, "QUBIT_EF")
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

        ##################################################################
        #################### Imag Characteristic for alpha3 ##############
        ##################################################################

        # Reboot
        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)
        qua.align()

        # Coherent state preparation
        qua.update_frequency(cav.name, int(-39.09e6), keep_phase=True)
        cav.play("cohstate_3_short", ampx=1)
        qua.update_frequency(cav.name, cav.int_freq)

        # Evolution
        qua.wait(1250 * 2, cav.name)
        qua.align()

        # Bias qubit to ECD point
        flux.play("constcos80ns_tomo_RO_4_E2pF2pG2pH2", ampx=-0.0696)
        qua.wait(25, cav.name, qubit.name)

        # Characteristic function
        Char_2D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            self.x,
            self.y,
            delay=self.delay,
            measure_real=False,
            tomo_phase=-0.16329,
            correction_phase=-0.011106,
        )

        # Measure qubit state
        qua.wait(int(750 // 4), rr.name, "QUBIT_EF")
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

        ##################################################################
        #################### Imag Characteristic for alpha4 ##############
        ##################################################################

        # Reboot
        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)
        qua.align()

        # Coherent state preparation
        qua.update_frequency(cav.name, int(-39.09e6), keep_phase=True)
        cav.play("cohstate_4_short", ampx=1)
        qua.update_frequency(cav.name, cav.int_freq)

        # Evolution
        qua.wait(1250 * 2, cav.name)
        qua.align()

        # Bias qubit to ECD point
        flux.play("constcos80ns_tomo_RO_4_E2pF2pG2pH2", ampx=-0.0696)
        qua.wait(25, cav.name, qubit.name)

        # Characteristic function
        Char_2D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            self.x,
            self.y,
            delay=self.delay,
            measure_real=False,
            tomo_phase=-0.16329,
            correction_phase=-0.011106,
        )

        # Measure qubit state
        qua.wait(int(750 // 4), rr.name, "QUBIT_EF")
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()

        ##################################################################
        #################### Imag Characteristic for alpha5 ##############
        ##################################################################

        # Reboot
        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)
        qua.align()

        # Coherent state preparation
        qua.update_frequency(cav.name, int(-39.09e6), keep_phase=True)
        cav.play("cohstate_5_short", ampx=1)
        qua.update_frequency(cav.name, cav.int_freq)

        # Evolution
        qua.wait(1250 * 2, cav.name)
        qua.align()

        # Bias qubit to ECD point
        flux.play("constcos80ns_tomo_RO_4_E2pF2pG2pH2", ampx=-0.0696)
        qua.wait(25, cav.name, qubit.name)

        # Characteristic function
        Char_2D_singledisplacement(
            cav,
            qubit,
            self.char_func_displacement,
            self.qubit_pi,
            self.qubit_pi2,
            self.x,
            self.y,
            delay=self.delay,
            measure_real=False,
            tomo_phase=-0.16329,
            correction_phase=-0.011106,
        )

        # Measure qubit state
        qua.wait(int(750 // 4), rr.name, "QUBIT_EF")
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()


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
        "reps": 7000,
        "wait_time": 0.3e6,
        "fetch_period": 30,  # time between data fetching rounds in sec
        "delay": 116,  # wait time between opposite sign displacements
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_pi": "gaussian_pi_short_ecd",
        "qubit_pi2": "gaussian_pi2_short_ecd",
        "char_func_displacement": "ecd2_displacement_alt",
        "cav_state_op": "_",
        "measure_real": "_",
        # "single_shot": True,
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": None,
        "skip_plot": True,
    }

    experiment = CharacteristicFunction2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
