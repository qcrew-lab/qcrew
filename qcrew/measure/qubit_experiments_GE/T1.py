"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
from lmfit import Parameters

# ---------------------------------- Class -------------------------------------
# delete this comment


class T1(Experiment):

    name = "T1"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="exp_decay", **other_params):

        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qubit.play(self.qubit_op)  # play pi qubit pulse
        qua.wait(self.x)  # wait for partial qubit decay
        qua.align()  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

    def data_analysis(self, fit_params):
        tau_ns = fit_params["tau"].value * 4
        fit_params.add("tau_ns", tau_ns)
        return fit_params


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
<<<<<<< Updated upstream
    x_start = 10
    x_stop = 20e3
    x_step = 400
    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 5000,
        "wait_time": 80000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "pi",
        "single_shot": True,
        #"plot_quad": "I_AVG",
=======
    x_start = int(0)
    x_stop = int(10e3)
    x_step = int(100)

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 60000,
        "wait_time": 200000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "constant_pi_pulse",
        "single_shot": False,
        "plot_quad": "Z_AVG"
>>>>>>> Stashed changes
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
    }

    experiment = T1(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
