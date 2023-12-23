"""
A python class describing a power rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------


class PowerRabi(Experiment):

    name = "power_rabi-double_rr"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn="sine", **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0524) #-0.5625
        qua.wait(500, qubit.name)
        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        qua.align()
        
        
        # first readout: Preselection
        flux.play("constcos80ns_tomo_RO_tomo_E2pF2pG2pH2", ampx=0.0524) #-0.5625
        qua.wait(int(30 // 4), rr.name, "QUBIT_EF")  # ns
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state
        # qua.wait(int(1000 // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        qua.align()  # wait qubit pulse to end
        qua.wait(50, rr.name, "QUBIT_EF")
        qua.play("digital_pulse", "QUBIT_EF")
        rr.measure((self.I, self.Q), ampx=0)  # measure qubit state
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution ----------------------------------

if __name__ == "__main__":

    amp_start = -1.9
    amp_stop = 1.91
    amp_step = 0.1
    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 10000,
        "wait_time": 80000,
        "x_sweep": (amp_start, amp_stop + amp_step / 2, amp_step),
        "qubit_op": "gaussian_pi_rr",
        # "plot_quad": "I_AVG",
        "single_shot": True,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse amplitude scaling",
        "skip_plot": True,
    }

    experiment = PowerRabi(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)