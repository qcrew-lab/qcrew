"""
A python class describing a DRAG pulse calibration using QM.
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
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_pi_op, qubit_pi2_op, fit_fn="linear", **other_params):

        self.qubit_pi_op = qubit_pi_op
        self.qubit_pi2_op = qubit_pi2_op
        self.fit_fn = fit_fn

        self.gate_list = [
            (self.qubit_pi_op, 0.25, self.qubit_pi2_op, 0.00, "YpX9"),  # YpX9
            (self.qubit_pi_op, 0.00, self.qubit_pi2_op, 0.25, "XpY9"),  # XpY9
        ]

        # Assign one sweep value for each time QUA_stream_results method is executed in
        # the pulse sequence. Is used for plotting with correct labels.
        self.internal_sweep = [x[4] for x in self.gate_list]  # select gate names

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (qubit, rr, flux) = self.modes  # get the modes

        for gate_pair in self.gate_list:
            gate1_rot, gate1_axis, gate2_rot, gate2_axis, _ = gate_pair

            qua.reset_frame(qubit.name)
            qua.align()

            # qua.update_frequency(qubit.name, int(-176.4e6))
            # flux.play("constcos80ns_1000ns_E2pF2pG2pH2", ampx=-0.0565)
            qua.wait(int(120 // 4), qubit.name)

            # Play the first gate
            # The DRAG correction is scaled by self.x
            qubit.play(gate1_rot, ampx=(1.0, 0.0, 0.0, self.x), phase=gate1_axis)

            # Play the second gate
            # The DRAG correction is scaled by self.x
            qubit.play(gate2_rot, ampx=(1.0, 0.0, 0.0, self.x), phase=gate2_axis)

            qua.wait(int(1000 // 4), qubit.name)
            qua.align(qubit.name, rr.name, "QUBIT_EF")  # align measurement
            qua.play("digital_pulse", "QUBIT_EF")
            rr.measure((self.I, self.Q), ampx=0)  # measure qubit state
            if self.single_shot:  # assign state to G or E
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )

            qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset
            qua.align(qubit.name, rr.name)  # align to the next gate pair
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -0.15
    x_stop = -0.07
    x_step = 0.005

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 200000,
        "wait_time": 80000,
        "x_sweep": (x_start, x_stop + x_step / 2, x_step),
        "qubit_pi_op": "gaussian_pi_short_ecd",
        "qubit_pi2_op": "gaussian_pi2_short_ecd",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        # "fetch_period": 3,
    }

    plot_parameters = {
        "xlabel": "DRAG pulse amplitude scaling",
    }

    experiment = DRAGCalibration(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
