"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QSwitch2D(Experiment):

    name = "q_switching_2D"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, cavity_drive_detuning, qubit_op, cav_op, fit_fn=None, **other_params):

        self.cav_op = cav_op  # coh1 pulse
        self.qubit_op = qubit_op  # pi pulse
        self.cav_drive_detuning = cavity_drive_detuning
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr= self.modes  # get the modes

        # qua.update_frequency(cav.name, cav.int_freq)
        cav.play(self.cav_op)  

        qua.update_frequency(cav.name, cav.int_freq + self.cav_drive_detuning)
        qua.update_frequency(rr.name, rr.int_freq + self.cav_drive_detuning + self.x)
        qua.align(rr.name, cav.name)
        rr.play("qswitch_pulse", duration=self.y)  # play pi qubit pulse
        cav.play("qswitch_pulse", duration=self.y)  # play pi qubit pulse
        qua.align(rr.name, cav.name, qubit.name)
        qua.update_frequency(qubit.name, qubit.int_freq)
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(rr.name, qubit.name)
        qua.update_frequency(rr.name, rr.int_freq)
        rr.measure((self.I, self.Q))  # measure qubit state
        
        
        if self.single_shot:
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -10e6
    x_stop = 10e6
    x_step = 0.5e6
    
    y_start = 64 // 4
    y_stop = 40e3 // 4
    y_step = 4e3 // 4

    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 50000,
        "wait_time": 1500e3,
        "x_sweep": (int(x_start), int(x_stop + x_step/2), int(x_step)),
        "y_sweep": (int(y_start), int(y_stop + y_step/2), int(y_step)),
        "qubit_op": "gaussian_pi_selective_pulse3",
        "cav_op": "cohstate1",
        "cavity_drive_detuning": int(100e6),
        "fetch_period": 4,
        "single_shot": False,
    }

    plot_parameters = {
        "xlabel": "Frequency detuning (Hz)",
        "ylabel": "Drive legnth (clock cycles)",
        "plot_type": "2D",
    }

    experiment = QSwitch2D(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
