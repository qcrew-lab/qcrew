  """
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------
class StarkShift(Experiment):
    name = "qubit_stark_shift"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, res_drive = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        res_drive.play("res_drive", ampx=self.y)  # Play continuous pump
        # qua.wait(int(100 / 4), qubit.name)
        qubit.play(self.qubit_op)  # play qubit pi pulse
        qua.align()
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    amp_start = 0.0
    amp_stop = 1.7
    amp_step = 0.1

    freq_start = 175e6
    freq_stop = 178e6
    freq_step = 0.02e6

    parameters = {
        "modes": ["QUBIT", "RR", "RR_DRIVE"],
        "reps": 2000,
        "wait_time": 500e3,
        "x_sweep": (int(freq_start), int(freq_stop + freq_step / 2), int(freq_step)),
        "qubit_op": "qubit_gaussian_sel_pi_pulse",
        "fetch_period": 4,
        "y_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "ylabel": "Pump amplitude scaling",
        "plot_type": "2D",
    }

    experiment = StarkShift(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
