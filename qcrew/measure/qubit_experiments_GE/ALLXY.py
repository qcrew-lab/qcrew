"""
A python class describing an ALLXY experiment using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class ALLXY(Experiment):

    name = "ALLXY"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_pi_op",  # Qubit pi operation
        "qubit_pi2_op",  # Qubit pi/2 operation
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_pi_op, qubit_pi2_op, fit_fn=None, **other_params):

        self.qubit_pi_op = qubit_pi_op
        self.qubit_pi2_op = qubit_pi2_op
        self.fit_fn = fit_fn

        self.gate_list = [
            ("idle", 0.00, "idle", 0.00, "IdId"),
            (self.qubit_pi_op, 0.00, self.qubit_pi_op, 0.00, "XpXp"),
            (self.qubit_pi_op, 0.25, self.qubit_pi_op, 0.25, "YpYp"),
            (self.qubit_pi_op, 0.00, self.qubit_pi_op, 0.25, "XpYp"),
            (self.qubit_pi_op, 0.25, self.qubit_pi_op, 0.00, "YpXp"),
            (self.qubit_pi2_op, 0.00, "idle", 0.00, "X9Id"),
            (self.qubit_pi2_op, 0.25, "idle", 0.00, "Y9Id"),
            (self.qubit_pi2_op, 0.00, self.qubit_pi2_op, 0.25, "X9Y9"),
            (self.qubit_pi2_op, 0.25, self.qubit_pi2_op, 0.00, "Y9X9"),
            (self.qubit_pi2_op, 0.00, self.qubit_pi_op, 0.25, "X9Yp"),
            (self.qubit_pi2_op, 0.25, self.qubit_pi_op, 0.00, "Y9Xp"),
            (self.qubit_pi_op, 0.00, self.qubit_pi2_op, 0.25, "XpY9"),
            (self.qubit_pi_op, 0.25, self.qubit_pi2_op, 0.00, "YpX9"),
            (self.qubit_pi2_op, 0.00, self.qubit_pi_op, 0.00, "X9Xp"),
            (self.qubit_pi_op, 0.00, self.qubit_pi2_op, 0.00, "XpX9"),
            (self.qubit_pi2_op, 0.25, self.qubit_pi_op, 0.25, "Y9Yp"),
            (self.qubit_pi_op, 0.25, self.qubit_pi2_op, 0.25, "YpY9"),
            (self.qubit_pi_op, 0.00, "idle", 0.00, "XpId"),
            (self.qubit_pi_op, 0.25, "idle", 0.00, "YpId"),
            (self.qubit_pi2_op, 0.00, self.qubit_pi2_op, 0.00, "X9X9"),
            (self.qubit_pi2_op, 0.25, self.qubit_pi2_op, 0.25, "Y9Y9"),
        ]

        # Assign one sweep value for each time QUA_stream_results method is executed in
        # the pulse sequence. Is used for plotting with correct labels.
        self.internal_sweep = [x[4] for x in self.gate_list]  # select gate names

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (qubit, rr) = self.modes  # get the modes

        for gate_pair in self.gate_list:
            gate1_rot, gate1_axis, gate2_rot, gate2_axis, _ = gate_pair

            qua.reset_frame(qubit.name)

            # Play the first gate
            if gate1_rot != "idle":
                qubit.play(gate1_rot, phase=gate1_axis)

            # Play the second gate
            if gate2_rot != "idle":
                qubit.play(gate2_rot, phase=gate2_axis)

            qua.align(qubit.name, rr.name)  # align gates to measurement pulse

            rr.measure((self.I, self.Q))  # measure transmitted signal

            if self.single_shot:  # assign state to G or E
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )

            qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

            qua.align(qubit.name, rr.name)  # align to the next gate pair

            self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 20000,
        "wait_time": 100000,
        "qubit_pi_op": "pi",
        "qubit_pi2_op": "pi2",
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Gate sequence",
    }

    experiment = ALLXY(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
