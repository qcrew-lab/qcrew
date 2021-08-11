"""
A python class describing a readout resonator spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class DRAGCalibration(Experiment):

    name = "DRAG_calibration"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_pi_op",  # Qubit pi operation
        "qubit_pi2_op",  # Qubit pi/2 operation
    }

    def __init__(self, qubit_pi_op, qubit_pi2_op, **other_params):

        self.qubit_pi_op = qubit_pi_op
        self.qubit_pi2_op = qubit_pi2_op

        self.gate_list = [
            (self.qubit_pi_op, 0.25, self.qubit_pi2_op, 0.00, "YpX9"),  # YpX9
            (self.qubit_pi_op, 0.00, self.qubit_pi2_op, 0.25, "XpY9"),  # XpY9
        ]

        # Num of times QUA_stream_results method is executed in the pulse sequence. Is
        # used in buffering.
        self.reshape = len(self.gate_list)

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
            # The DRAG correction is scaled by self.x
            qubit.play(gate1_rot, ampx=(1.0, 0.0, 0.0, self.x), phase=gate1_axis)

            # Play the second gate
            # The DRAG correction is scaled by self.x
            qubit.play(gate2_rot, ampx=(1.0, 0.0, 0.0, self.x), phase=gate2_axis)

            qua.align(qubit.name, rr.name)

            rr.measure((self.I, self.Q))  # measure transmitted signal
            qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

            self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 20000,
        "wait_time": 10000,
        "x_sweep": (-0.2, 0.2, 0.02),
        "qubit_pi_op": "pi",
        "qubit_pi2_op": "pi2",
    }

    experiment = DRAGCalibration(**parameters)
    prof.run(experiment)
