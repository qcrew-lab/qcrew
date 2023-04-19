"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitSpecNumbSplit(Experiment):

    name = "qubit_spec_number_split"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "cav_op"
    
    }

    def __init__(self, qubit_op, cav_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.fit_fn = fit_fn
     
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr , cavb= self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        cavb.play(self.cav_op, ampx=1)
        qua.align(qubit.name, cavb.name)
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end 
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -33e6
    x_stop = -29e6
    x_step = 0.02e6

    parameters = {
        "modes": ["QUBIT", "RR", "CAVB"],
        "reps": 50000,
        "wait_time": 80000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        # "y_sweep": (0,0.005,0.01,0.02),
        "qubit_op": "gaussian_pi_selective_pulse",
        "cav_op": "coherent1",
        "plot_quad": "Q_AVG"
    }   

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = QubitSpecNumbSplit(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
