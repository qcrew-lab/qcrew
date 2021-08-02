"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
# --------------------------------- Imports ------------------------------------
from qm import qua

from qcrew.helpers.parametrizer import Parametrized
from typing import ClassVar
from qcrew.measure.Experiment import Experiment
from qcrew.control import Stagehand
import qua_macros as macros

# ---------------------------------- Class -------------------------------------


class T1(Experiment):

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "mode_names",  # names of the modes used in the experiment
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # Fit function
    }

    def __init__(self, modes, qubit_op, fit_fn="exp_decay", **other_params):

        self.mode_names = modes  # mode names for saving metadata
        self.modes = None  # is updated with mode objects by the professor
        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qubit.play(self.qubit_op)  # play pi qubit pulse
        qua.wait(int(self.x // 4), qubit.name)  # wait for partial qubit decay
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        macros.stream_results(self.var_list)  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ("QUBIT", "RR"),
        "reps": 20000,
        "wait_time": 32000,
        "x_sweep": (int(16), int(1000 + 40 / 2), int(40)),
        "qubit_op": "gaussian_pulse",
    }

    experiment = T1(**parameters)

    # The following will be done by the professor
    with Stagehand() as stage:

        mode_tuple = tuple()
        for mode_name in experiment.mode_names:
            mode_tuple += (getattr(stage, mode_name),)

        experiment.modes = mode_tuple

        power_rabi = experiment.QUA_sequence()

        #################   RUN MEASUREMENT   ##################

        job = stage.QM.execute(power_rabi)
