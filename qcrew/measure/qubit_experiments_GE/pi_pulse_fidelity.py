"""
A python class describing a qubit pi pulse fidelity measurement.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class Pi_Pulse_Fidelity(Experiment):

    name = "pi_pulse_fidelity"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="sine", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Plays a qubit π pulse repeatedly and measures
        """
        qubit, rr = self.modes  # get the modes

        for number in range(self.x):
            qubit.play(self.qubit_op,)  # play qubit pulse

        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    """
    We will use a previously calibrated pi pulse and play it repeatedly, 
    to determine the fidelity of the process. Every odd seqeuence should give
    a state of |e>, and every even sequence should give a state of |g>
    """

    n_start = 0
    n_stop = 20
    n_step = 1

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 20000,
        "wait_time": 150000,
        "x_sweep": (n_start, n_stop + n_step // 2, n_step),
        "qubit_op": "qubit_numerical_pulse",
        "single_shot": False,
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {
        "xlabel": "Number of π Pulses",
    }

    experiment = Pi_Pulse_Fidelity(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
