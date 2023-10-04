"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------
class NSplitSpectroscopy(Experiment):
    name = "number_split_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, fit_fn,rr_drive, **other_params
    ):
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.rr_drive = rr_drive

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq)

        
        rr.play(self.rr_drive, duration = 104,ampx = self.y)

        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes
        qua.wait(int(250))
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.align(qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4))  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    # x_start = 176.4e6
    # x_stop = 178.4e6
    # x_step = 0.02e6

    x_start = 174.4e6
    x_stop = 180.4e6
    x_step = 0.1e6

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 500,
        "wait_time": 500e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        # "y_sweep": [0.8, 1.0, 1.2, 1.4, 1.6 , 1.8],
        "qubit_op": "qubit_gaussian_416ns_pi_pulse",
        "rr_drive": "constant_drive",
        # "plot_quad": "I_AVG",
        "single_shot": "True",
        "fit_fn": None,
        "fetch_period": 1,
    }

    plot_parameters = {"xlabel": "Qubit pulse frequency (Hz)", "plot_err": None}

    experiment = NSplitSpectroscopy(**parameters)
    experiment.name = "PND_RR_drive" 
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
