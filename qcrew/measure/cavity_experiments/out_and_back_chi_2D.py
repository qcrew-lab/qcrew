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


class OutAndBack(Experiment):

    name = "out_and_back"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_displacement",  # operation for displacing the cavity
        "qubit_pi",  # operation used for exciting the qubit
        "qubit_pi_selective",
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        cav_displacement,
        qubit_pi,
        qubit_pi_selective,
        fit_fn="gaussian",
        **other_params
    ):

        self.cav_displacement = cav_displacement
        self.qubit_pi_selective = qubit_pi_selective
        self.qubit_pi = qubit_pi
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """

        
        qubit, cav, rr = self.modes  # get the modes
        qua.reset_frame(cav.name)
        qua.reset_phase(qubit.name)
        qua.reset_phase(cav.name)
        cav.play(self.cav_displacement)  # displace cavity
        qua.align(qubit.name, cav.name)  # align all modes

        qubit.play(self.qubit_pi)  # put qubit into excited state to start rotation
        qua.align(qubit.name, cav.name)

        qua.wait(self.x, cav.name)  # wait for state to rotate
        qua.assign(self.phase, self.y)
        cav.play(self.cav_displacement, phase=self.phase)  # displace qubit back
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

    # wait time tau in clock cycle
    x_start = 4
    x_stop = 1224
    x_step = 20

    # disp_phase
    y_start = 0
    y_stop = 1
    y_step = 0.01
    parameters = {
        "modes": ["QUBIT", "CAVITY", "RR"],
        "reps": 50000,
        "wait_time": 200e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": ((y_start), (y_stop + y_step / 2), (y_step)),
        "qubit_pi": "pi",
        "qubit_pi_selective": "pi_selective_500",
        "cav_displacement": "bob_large_displacement",
        "fetch_period": 4,
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
        "xlabel": "delay in clockcycles",  # beta of (ECD(beta))
        "ylabel": "displacement pulse phase",
        "plot_type": "2D",
        "cmap": "bwr",
    }

    experiment = OutAndBack(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
