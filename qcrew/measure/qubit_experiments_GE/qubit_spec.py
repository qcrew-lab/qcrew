"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar
from qcrew.control import Stagehand
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitSpectroscopy(Experiment):
    name = "qubit_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "cav_op",
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
        qua.update_frequency(qubit.name, self.x) 
        # cav.play(self.cav_op, ampx = 1.2)# update resonator pulse frequency
        # qua.align()
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        # qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    # x_start = 177.30e6
    # x_stop = 177.45e6
    # x_step = 0.005e6

    x_start = -60e6 - 8e6
    x_stop = -60e6 + 2e6 
    x_step = 0.02e6

    with Stagehand() as stage:
        qubit = stage.QUBIT

    parameters = {
        "modes": ["QUBIT", "CAV","RR"],
        "reps": 1000,
        "wait_time": 600e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "qubit_gaussian_sig250ns_pi_pulse",
        "cav_op":"coherent_1_long",
        # "qubit_op" : "cc_2000",
        "fit_fn": "gaussian",
        "single_shot": True,
        # "plot_quad": "I_AVG",
        # "plot_quad": "PHASE",
        "fetch_period": 4,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
        "plot_type": "1D",
        "plot_err": False,
    }

    experiment = QubitSpectroscopy(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
