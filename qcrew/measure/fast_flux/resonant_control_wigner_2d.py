"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class ResonantCtrlFastFluxWigner2D(Experiment):

    name = "resonant_ctrl_wigner_2d"

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

        flux.play("predist_pulse_2", ampx=-0.247)
        qua.wait(50, qubit.name)
        qua.update_frequency(qubit.name, int(-58.24e6))
        qubit.play(self.pi_01m, ampx=1)  # play pi pulse to (g,0)->(1,-)

        # Wigner 2d
        ## single displacement
        qua.align(cav.name, flux.name)
        qua.wait(50, cav.name)
        cav.play(
            self.cav_op,
            ampx=(self.x, -self.y, self.y, self.x),
            phase=0.5,
        )
        qua.align(cav.name, qubit.name)
        qua.update_frequency(qubit.name, int(-86.6e6))
        qubit.play(self.qubit_op_wigner)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4),
            cav.name,
            qubit.name,
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op_wigner)  # play pi/2 pulse around X

        # Measure cavity state
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        # cav.play(self.cav_op, ampx=self.x, phase=0)  # displacement in I direction
        # qua.align(cav.name, qubit.name)
        # qua.update_frequency(qubit.name, int(-86.6e6))
        # qubit.play(self.qubit_op_wigner)  # play pi/2 pulse around X
        # qua.wait(
        #     int(self.delay // 4),
        #     cav.name,
        #     qubit.name,
        # )  # conditional phase gate on even, odd Fock state
        # qubit.play(self.qubit_op_wigner)  # play pi/2 pulse around X

        # # Measure cavity state
        # qua.align(qubit.name, rr.name)  # align measurement
        # rr.measure((self.I, self.Q))  # measure transmitted signal

        # # wait system reset
        # qua.align(cav.name, qubit.name, rr.name)
        # # rr.play("constant_pulse", duration=5e3, ampx=1)
        # # cav.play("constant_pulse", duration=5e3, ampx=0.04)
        # qua.wait(int(self.wait_time // 4), cav.name)

        # if self.single_shot:  # assign state to G or E
        #     qua.assign(
        #         self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
        #     )

        # self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.2
    x_stop = 1.2
    x_step = 0.1

    y_start = -1.2
    y_stop = 1.2
    y_step = 0.1

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX", "CAVITY"],
        "reps": 10000,
        "wait_time": 10e6,  # ns
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "constant_pi",
        "qubit_op_wigner": "constant_pi2_short",
        "pi_01m": "gaussian_sel_pi2_01m",
        "cav_op": "const_cohstate_3",
        # "plot_quad": "I_AVG",
        "fit_fn": "gaussian",
        "delay": 500,  # pi/chi 208
        "fetch_period": 5,
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": None,
    }

    experiment = ResonantCtrlFastFluxWigner2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
