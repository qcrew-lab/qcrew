"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np

# ---------------------------------- Class -------------------------------------

# short pi2
# displace cavity real axis by 1
# wait pi/chi 289
# displace cavity real axis by 1
# selective pi

# Wigner


class WignerFunctionQCmap(Experiment):
    name = "wigner_function_QC_map"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",  # describe...
    }

    def __init__(
        self, cav_op, qubit_op, qubit_sel_op, fit_fn=None, delay=4, **other_params
    ):
        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.qubit_sel_op = qubit_sel_op
        self.fit_fn = fit_fn
        self.delay = delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.reset_frame(qubit.name)

        # CAT STATE
        # cav.play(
        #     "cc_coherent_1", ampx=1, phase=-0.25
        # )  # change to disp first before pi2, reduces some coherent errors
        # qua.align(cav.name, qubit.name)
        
        # qubit.play('qubit_gaussian_short_pi_pulse')
        # qubit.play('qubit_gaussian_short_pi_pulse')
        # qubit.play(
        #     "qubit_gaussian_short_pi2_pulse", phase=0
        # )  # play pi/2 pulse around X
        # qua.align(cav.name, qubit.name)
        # qua.wait(
        #     int(172.0 // 4), cav.name, qubit.name
        # )  # conditional phase gate on even, odd Fock state
        # # cav.play('cc_coherent_1', ampx=1, phase=-0.25)
        # # qua.align(cav.name, qubit.name)
        # # qubit.play(self.qubit_sel_op)  # play pi/2 pulse around X

        # WIGNER
        qua.align(cav.name, qubit.name)
        cav.play(self.cav_op, ampx=(self.x, self.y, -self.y, self.x), phase=0.25)
        qua.align(cav.name, qubit.name)
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4), cav.name, qubit.name
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.8
    x_stop = 1.8
    x_step = 0.2

    y_start = -1.8
    y_stop = 1.8
    y_step = 0.2

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 500,
        "wait_time": 10e6,
        "delay": 288,  # 294, #750/8,  # pi/chi
        "x_sweep": (
            x_start,
            x_stop + x_step / 2,
            x_step,
        ),  # ampitude sweep of the displacement pulses in the ECD
        "y_sweep": (
            y_start,
            y_stop + y_step / 2,
            y_step,
        ),
        "qubit_op": "qubit_gaussian_short_pi2_pulse",
        "qubit_sel_op": "qubit_gaussian_lesssel_pi_pulse",
        "cav_op": "coherent_1_long",
        "single_shot": True,
        # "plot_quad":"I_AVG",
        "fetch_period": 4,  # time between data fetching rounds in sec
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": False,
    }

    experiment = WignerFunctionQCmap(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
