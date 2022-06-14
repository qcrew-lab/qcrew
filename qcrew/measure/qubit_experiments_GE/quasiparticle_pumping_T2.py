"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QPPumpingT2(Experiment):

    name = "quasiparticle_pumping_T2"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_pi_op",  # pi operation used quasiparticle pumping
        "qubit_pi2_op",  # pi2 operation used for the T2 experiment
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_pi_op,
        qubit_pi2_op,
        dT,
        detuning=0,
        fit_fn="exp_decay_sine",
        **other_params
    ):

        self.qubit_pi_op = qubit_pi_op  # pi pulse
        self.qubit_pi2_op = qubit_pi2_op  # pi pulse
        self.dT = dT  # time between pulses in the pumping sequence
        self.detuning = detuning  # frequency detuning of qubit operation
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        # quasiparticle pumping sequence
        k = qua.declare(int)
        with qua.for_(var=k, init=0, cond=k < self.y, update=k + 1):
            qua.wait(
                int(self.dT // 4), qubit.name
            )  # wait for qubit to interact with QPs
            qubit.play(self.qubit_pi_op)  # excite the qubit with a pi pulse

        qua.wait(int(self.dT // 4), qubit.name)  # wait for qubit to interact with QPs
        qua.update_frequency(qubit.name, qubit.int_freq + self.detuning)  # detune
        qubit.play(self.qubit_pi2_op)  # play half pi qubit pulse
        qua.wait(self.x, qubit.name)  # wait for partial qubit decay
        qubit.play(self.qubit_pi2_op)  # play half pi qubit pulse

        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = 10
    x_stop = 12000
    x_step = 150
    detuning = 200e3
    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 20000,
        "wait_time": 1500000,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (0, 6),
        "qubit_pi_op": "pi",
        "qubit_pi2_op": "pi2",
        "detuning": detuning,
        "dT": 50000,
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Number of pi pulses",
    }

    experiment = QPPumpingT2(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
