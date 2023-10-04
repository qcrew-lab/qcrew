"""
A python class describing an ECD calibration experiment, following Campagne-Ibarq et al. 2020 Quantum Error correction of a qubit encoded in a grid....
It is essentially a characteristic function (C(\beta)) measurement of the vacuum state.

NOT FINISHED
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np


# ---------------------------------- Class -------------------------------------


class CharacteristicFunction1D(Experiment):
    name = "characteristic_function_1D"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_state_op",
        "cav_op",  # operation for displacing the cavity
        "qubit_op1",
        "qubit_op2",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
        "measure_real",
    }

    def __init__(
        self,
        cav_state_op,
        cav_op,
        qubit_op1,
        qubit_op2,
        fit_fn=None,
        delay=4,
        measure_real=True,
        **other_params
    ):
        self.cav_state_op = cav_state_op
        self.cav_op = cav_op
        self.qubit_op1 = qubit_op1
        self.qubit_op2 = qubit_op2
        self.fit_fn = fit_fn
        self.delay = delay
        self.measure_real = measure_real

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)

        ECD_factor_1 = np.cos(1.36e-3 * 2 * np.pi * self.delay / 2)
        ECD_factor_2 = np.cos(1.36e-3 * 2 * np.pi * self.delay)

        if 0:
            cav.play(self.cav_state_op, phase=0.25)  # to create a coherent state
            qua.align(cav.name, qubit.name)
            # qubit.play(self.qubit_op1)  # bring qubit into superposition

        # Apply ECD for state preparation
        if 1:
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_state_op, ampx=1, phase=0.25
            )  # First positive displacement
            qua.wait(int(self.delay // 4), cav.name)
            cav.play(
                self.cav_state_op,
                ampx=-1 * ECD_factor_1,
                phase=0.25,
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(self.qubit_op2)  # play pi to flip qubit around X
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_state_op,
                ampx=-1 * ECD_factor_1,
                phase=0.25,
            )  # Second negative displacement
            qua.wait(int(self.delay // 4), cav.name)
            cav.play(
                self.cav_state_op,
                ampx=1 * ECD_factor_2,
                phase=0.25,
            )  # Second positive displacement
            qua.align(qubit.name, cav.name)
            qubit.play(self.qubit_op2)
            qua.align(qubit.name, cav.name)

        # start char_function measurement
        qubit.play(self.qubit_op1)  # play pi/2 pulse around X

        if 1:  # large chi
            # start ECD gate
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(self.cav_op, ampx=self.x, phase=0)  # First positive displacement
            qua.wait(int(self.delay // 4), cav.name)
            cav.play(
                self.cav_op,
                ampx=-np.cos(1.36e-3 * 2 * np.pi * self.delay / 2) * self.x,
                phase=0,
            )  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(self.qubit_op2)  # play pi to flip qubit around X
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(
                self.cav_op,
                ampx=-np.cos(1.36e-3 * 2 * np.pi * self.delay / 2) * self.x,
                phase=0,
            )  # Second negative displacement
            qua.wait(int(self.delay // 4), cav.name)
            cav.play(
                self.cav_op,
                ampx=np.cos(1.36e-3 * 2 * np.pi * self.delay) * self.x,
                phase=0,
            )  # Second positive displacement
            qua.align(qubit.name, cav.name)

        if 0:  # small chi
            # start ECD gate
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(self.cav_op, ampx=self.x, phase=0)  # First positive displacement
            qua.wait(int(self.delay // 4), cav.name)
            cav.play(self.cav_op, ampx=-self.x, phase=0)  # First negative displacement
            qua.align(qubit.name, cav.name)
            qubit.play(self.qubit_op2)  # play pi to flip qubit around X
            qua.align(cav.name, qubit.name)  # wait for qubit pulse to end
            cav.play(self.cav_op, ampx=-self.x, phase=0)  # Second negative displacement
            qua.wait(int(self.delay // 4), cav.name)
            cav.play(self.cav_op, ampx=self.x, phase=0)  # Second positive displacement
            qua.align(qubit.name, cav.name)

        qubit.play(
            self.qubit_op1, phase=0.0 if self.measure_real else 0.25
        )  # play pi/2 pulse around X or SY, to measure either the real or imaginary part of the characteristic function

        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.8
    x_stop = 1.8
    x_step = 0.05

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 500,
        "wait_time": 10e6,
        "fetch_period": 5,  # time between data fetching rounds in sec
        "delay": 60,  # wait time between opposite sign displacements
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "qubit_op1": "qubit_gaussian_short_pi2_pulse",
        "qubit_op2": "qubit_gaussian_short_pi_pulse",
        "cav_state_op": "cc_ECD_2",
        "cav_op": "cc_ECD_2",
        # "ECD_phase": 0
        "measure_real": True,  # measure real part of char function if True, imag Part if false
    }

    plot_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
    }

    experiment = CharacteristicFunction1D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
