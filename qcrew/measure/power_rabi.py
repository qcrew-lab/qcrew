"""
A python class describing a power rabi measurement using the QM 
system. 
This class serves as a QUA script generator with user-defined parameters. It 
also defines how the information is retrieved from result handles.
"""
# --------------------------------- Imports ------------------------------------
import qcrew.measure.professor as prof
from qm import qua

from qcrew.measure.Experiment import Experiment
import qua_macros as macros

# ---------------------------------- Class -------------------------------------


class PowerRabi(Experiment):
    def __init__(
        self, qubit_mode, rr_mode, qubit_op, readout_op, fit_fn=None, **other_params
    ):

        # Get attributes
        self.qubit_mode = qubit_mode
        self.rr_mode = rr_mode
        self.qubit_op = qubit_op
        self.readout_op = readout_op
        self.fit_fn = fit_fn

        # Passes remaining parameters to parent
        super().__init__(**other_params)

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """

        self.qubit_mode.play(self.qubit_op, ampx=self.x)
        qua.align(self.qubit_mode.name, self.rr_mode.name)
        self.rr_mode.measure((self.I, self.Q))
        qua.wait(int(self.wait_time // 4), self.qubit_mode.name)
        macros.stream_results(self.var_list)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ("QUBIT", "RR"),
        # "qubit_mode": qubit,
        # "rr_mode": rr,
        "reps": 200000,  # number of sweep repetitions
        "wait_time": 32000,  # delay between reps in ns, an integer multiple of 4 >= 16
        "x_sweep": (-1.9, 1.9 + 0.2 / 2, 0.2),  # x sweep is set by start, stop & step
        # "y_sweep": [True, False],  # x sweep is set by start, stop, and step
        "qubit_op": "gaussian_pulse",  # Operations to be used in the exp.
        # "readout_op": "readout",
        "fit_fn": "sine",  # name eof the fit function
    }
    experiment = PowerRabi(**parameters)
    prof.run(experiment)
