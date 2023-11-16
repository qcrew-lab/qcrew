"""
A python class describing a cavity T1 experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import qcrew.measure.qua_macros as macros

# ---------------------------------- Class -------------------------------------


class OutAndBackKerr(Experiment):

    name = "out_and_back_kerr"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_displacement",  # operation for displacing the cavity
        "qubit_pi",  # operation used for exciting the qubit
        "qubit_pi_selective",
        "delay",
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        cav_displacement,
        qubit_pi,
        qubit_pi_selective,
        delay,
        fit_fn="gaussian",
        **other_params
    ):

        self.cav_displacement = cav_displacement
        self.qubit_pi_selective = qubit_pi_selective
        self.qubit_pi = qubit_pi
        self.delay = delay
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """

        qubit, cav, rr = self.modes  # get the modes

        cav.play(self.cav_displacement, ampx=self.x)  # displace cavity
        qua.align(qubit.name, cav.name)  # align all modes


        qua.wait(self.delay, cav.name)  # wait for state to rotate
        qua.assign(self.phase, self.y)
        cav.play(
            self.cav_displacement, phase=self.phase, ampx=self.x
        )  # displace qubit back
        qua.align(qubit.name, cav.name)  # align all modes
        qubit.play(
            self.qubit_pi_selective
        )  # play conditional pi pulse to flip qubit if cav is in vac or close to vac
        qua.align(qubit.name, rr.name)  # align all modes

        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # tream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    # ampx
    x_start = 0.5
    x_stop = 1.9
    x_step = 0.03

    # disp_phase
    y_start = 0.1
    y_stop = 0.8
    y_step = 0.01

    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR"],
        "reps": 100000,
        "wait_time": 200e3,
        "x_sweep": ((x_start), (x_stop + x_step / 2), (x_step)),
        "y_sweep": ((y_start), (y_stop + y_step / 2), (y_step)),
        "delay": 1000,
        "qubit_pi": "gaussian_pi_short_ecd",
        "qubit_pi_selective": "gaussian_pi_320",
        "cav_displacement": "cohstate_5_short",
        "fetch_period": 20,
        "single_shot": False,
        "plot_quad": "I_AVG",
        "extra_vars": {
            "phase": macros.ExpVariable(
                var_type=qua.fixed,
                tag="phase",
                average=True,
                buffer=True,
                save_all=True,
            )
        },
    }

    plot_parameters = {
        "xlabel": "displacement pulse amp",  # beta of (ECD(beta))
        "ylabel": "displacement pulse phase",
        "plot_type": "2D",
        "cmap": "bwr",
    }

    experiment = OutAndBackKerr(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
