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

    _parameters: ClassVar[set[str]] = Experiment._parameters | {}

    def __init__(self, **other_params):

        self.gate_list = [
            ("pi", "Y", "pi2", "X", "YpX9"),  # YpX9
            ("pi", "X", "pi2", "Y", "XpY9"),  # XpY9
        ]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (qubit, rr) = self.modes  # get the modes

        for gate_pair in self.gate_list:
            gate1_rot, gate1_axis, gate2_rot, gate2_axis, _ = gate_pair

            qua.reset_frame(qubit.name)
            qua.align(qubit.name, rr.name)

            # First gate
            qubit.rotate(self, angle=gate1_rot, axis=gate1_axis)
    
            # Second pulse
            qubit.rotate(self, angle=gate2_rot, axis=gate2_axis)

            rr.measure((self.I, self.Q))  # measure transmitted signal
            qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

            self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ["QUBIT", "RR"],
        "reps": 20000,
        "wait_time": 10000,
        "x_sweep": (int(-50e6), int(50e6 + 0.2e6 / 2), int(0.2e6)),
        "y_sweep": (0.1, 1.5 + 0.05 / 2, 0.05),
    }

    experiment = DRAGCalibration(**parameters)
    prof.run(experiment)
