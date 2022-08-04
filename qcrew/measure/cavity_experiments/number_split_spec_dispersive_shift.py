"""
A python class describing a photon-number split spectroscopy sweeping the number of 
photons in the cavity using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class NSplitSpecDispersiveShift(Experiment):

    name = "number_split_spec_dispersive_shift"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
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
        qubit, cav, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        cav.play(self.cav_op, ampx=self.y)  # prepare cavity state
        qua.align(cav.name, qubit.name)  # align modes
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 47e6
    x_stop = 53e6
    x_step = 0.05e6

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 4000,
        "wait_time": 400000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": [0, 1.41],
        "qubit_op": "pi_selective_1",
        "cav_op": "constant_cos_cohstate_1",
        "fetch_period": 4,
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "trace_labels": ["<n> = 0", "<n> = 2"],
    }

    experiment = NSplitSpecDispersiveShift(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
