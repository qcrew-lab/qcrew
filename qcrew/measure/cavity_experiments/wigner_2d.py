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

        # cav.play(self.cav_op, ampx=-1, phase=0)

        # # Fock satae preparation
        if 0: 
            qubit.play("gaussian_pi")
            qua.align(flux.name, qubit.name)
            flux.play("predist_pulse_36",ampx=0.39)
            qua.align(cav.name, flux.name)
            qua.wait(50, cav.name)  # cc


        # Wigner
        cav.play(
            self.cav_op_wigner,
            ampx=(-self.y, self.x, -self.x, -self.y),
            phase=0.5,  # 0.25
        )
        qua.align(cav.name, qubit.name)
        # qua.update_frequency(qubit.name, int(-86.6e6))
        qubit.play(self.qubit_op_wigner, ampx=1)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4),
            cav.name,
            qubit.name,
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op_wigner, ampx=1)  # play pi/2 pulse around X

        # Measure cavity state
        #readout pulse
        qua.align()  # align modes
        flux.play("detuned_readout", ampx=-0.5)
        qua.wait(int((25) // 4), cav.name, qubit.name, rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -1.8
    x_stop = 1.8
    x_step = 0.1

    y_start = -1.8
    y_stop = 1.8
    y_step = 0.1

    parameters = {
        "modes": ["QUBIT", "RR", "CAVITY", "FLUX"],
        "reps": 1000,
        "wait_time": 0.55e6,  # ns
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "y_sweep": (y_start, y_stop + y_step / 2, y_step),
        "qubit_op": "gaussian_pi",
        "cav_op": "qctrl_fock_0p1",
        "qubit_op_wigner": "gaussian_pi2_short",
        "cav_op_wigner": "const_cohstate_1",
        "plot_quad": "I_AVG",
        # "single_shot": False,
        "fit_fn": "gaussian",
        "delay": 160,
        "fetch_period": 10,
    }

    plot_parameters = {
        "xlabel": "X",
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        "plot_err": None,
    }

    experiment = Wigner2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
