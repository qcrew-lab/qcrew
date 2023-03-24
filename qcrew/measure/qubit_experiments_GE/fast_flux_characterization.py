"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitSpectroscopy(Experiment):

    name = "qubit_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        self.internal_sweep = [24 * i for i in range(20)]  # select gate names

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, flux, rr = self.modes  # get the modes

        for delay in self.internal_sweep:
            flux.play("constant_pulse")
            if delay:   
                qua.wait(int(delay // 4), qubit.name)
            qubit.play(self.qubit_op, duration=100)  # play qubit pulse
            qua.align(qubit.name, rr.name)  # wait qubit pulse to end
            rr.measure((self.I, self.Q))  # measure transmitted signal
            qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 16  # 181.25e6
    x_stop = 250  # 181.5e6
    x_step = 10

    parameters = {
        "modes": ["QUBIT", "FLUX", "RR"],
        "reps": 100000000,
        "wait_time": 50000,
        # "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "constant_pulse",
        # "plot_quad": "PHASE",
        "fetch_period": 5,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse duration (clock cycles)",
    }

    experiment = QubitSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
