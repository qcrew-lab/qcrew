"""
A python class describing a readout resonator spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class DoubleReadout(Experiment):

    name = "double_readout"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
    }

    def __init__(self, fit_fn=None, **other_params):

        self.fit_fn = fit_fn
        self.internal_sweep = ["first_readout", "second_readout"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr,) = self.modes  # get the modes

        # first readout
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        qua.wait(1500, rr.name)
        # # second readout
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        qua.wait(int(self.wait_time // 4), rr.name)

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["RR"],
        "reps": 200000,
        "wait_time": 80000,  # 500ns*5 = 2.5us = 2500ns
        "fit_fn": "gaussian",
        "single_shot": True,
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
        "skip_plot": True,
    }

    experiment = DoubleReadout(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
