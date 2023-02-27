"""
A python class describing a photon-number dependent Readout Resonator frequency sweeping the number of 
photons in the cavity using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class NCavityResonatorShift(Experiment):

    name = "cavity_resonator_shift"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "fit_fn",  # fit function
    }

    def __init__(self, cav_op, fit_fn=None, **other_params):

        self.cav_op = cav_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        cav, rr = self.modes  # get the modes

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        cav.play(self.cav_op, ampx=self.y)  # prepare cavity state
        qua.align(cav.name, rr.name)  # align modes
        rr.measure((self.I, self.Q), ampx=1)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -50.175e6
    x_stop = -50.1e6
    x_step = 0.005e6

    parameters = {
        "modes": ["CAV", "RR"],
        "reps": 100000,
        "wait_time": 1.3e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": [0, 1.],
        "cav_op": "const_cos_pulse",
        "fetch_period": 7,
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
        "trace_labels": ["<n> = 0", "<n> = 1"],
    }

    experiment = NCavityResonatorShift(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
