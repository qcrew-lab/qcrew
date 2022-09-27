"""
A python class describing a readout resonator spectroscopy with qubit in ground and 
excited state using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class RRSpecDispersiveShift(Experiment):

    name = "rr_spec_dispersive_shift"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, fit_fn=None, **other_params):

        self.fit_fn = fit_fn
        self.cav_op = cav_op

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr, cav_a) = self.modes  # get the modes

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        cav_a.play(self.cav_op, ampx=self.y)
        qua.align(rr.name, cav_a.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -52e6
    x_stop = -48e6
    x_step = 0.04e6

    parameters = {
        "modes": ["RR", "CAV_Alice"],
        "reps": 10000,
        "wait_time": 100000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": [0.0, 1.0],
        "cav_op": "gaussian_pi_selective_pulse3",
        "plot_quad": "Z_AVG",
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
    }

    experiment = RRSpecDispersiveShift(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
