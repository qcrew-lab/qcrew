"""
for optimizing the max of vacuum in the origin using char func 1d 
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np
from qcrew.measure.qua_macros import *
import qcrew.measure.qua_macros as macros

# ---------------------------------- Class -------------------------------------


class CF_optimise(Experiment):

    name = "CF_optimise"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "ecd_displacement",  # operation for displacing the cavity
        "qubit_pi2",  # operation used for exciting the qubit
        "qubit_pi",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(
        self,
        ecd_displacement,
        qubit_pi,
        qubit_pi2,
        fit_fn="sine",
        delay=4,
        measure_real=True,
        **other_params
    ):

        self.ecd_displacement = ecd_displacement
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
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)

        if 0:
            rr.measure((self.I, self.Q))  # measure transmitted signal
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()  # align measurement
            qua.wait(int(20))
            qua.align()

        if 0:
            V_cat(
                cav,
                qubit,
                "constant_cos_ECD_3",
                self.qubit_pi,
                self.qubit_pi2,
                ampx=1,
                delay=self.delay,
                qubit_phase=0.25,
            )
            qua.align()

        ###################### do a first measurement  #####################
        # qua.align()
        # rr.measure((self.I, self.Q))  # measure transmitted signal
        # self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        # qua.align()  # align measurement
        # qua.wait(int(20))
        # qua.align()

        ###################### do a first measurement  #####################
        qua.reset_frame(qubit.name)
        qubit.play(self.qubit_pi2)
        # ECD(
        #     cav,
        #     qubit,
        #     self.ecd_displacement,
        #     self.qubit_pi,
        #     ampx=0,
        #     delay=self.delay,
        #     phase=0.25,
        #     qubit_phase=0.25,
        # )

        amp_test = 0

        qua.align()  # wait for qubit pulse to end
        cav.play(
            self.ecd_displacement, ampx=amp_test, phase=0.25
        )  # First positive displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(
            self.ecd_displacement, ampx=-amp_test, phase=0.25
        )  # First negative displacement
        qua.align()
        qua.reset_frame(qubit.name)
        qubit.play("pi", ampx=1.0, phase=0.0)  # play pi to flip qubit around X
        qua.align()  # wait for qubit pulse to end
        cav.play(
            self.ecd_displacement, ampx=-amp_test, phase=0.25
        )  # Second negative displacement
        qua.wait(int(self.delay // 4), cav.name)
        cav.play(
            self.ecd_displacement, ampx=amp_test, phase=0.25
        )  # Second positive displacement
        qua.align()
        qua.reset_frame(qubit.name)

        qubit.play(self.qubit_pi2, phase=self.x)

        # play pi/2 pulse around X or Y, to measure either the real or imaginary part of the characteristic function
        qua.align()  # align measurement
        rr.measure((self.I, self.Q))

        # wait system reset
        qua.wait(int(self.wait_time // 4))
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 0.0
    x_stop = 1.5
    x_step = 0.05

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 1000,
        "wait_time": 2e6,
        "fetch_period": 2,  # time between data fetching rounds in sec
        "delay": 80,  # pi/chi
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_pi2": "pi2",
        "qubit_pi": "pi",
        "ecd_displacement": "constant_cos_ECD_3",
        "single_shot": True,
        # "plot_quad": "I_AVG",
        "measure_real": True,
    }

    plot_parameters = {"xlabel": "X"}  # beta of (ECD(beta))

    experiment = CF_optimise(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
