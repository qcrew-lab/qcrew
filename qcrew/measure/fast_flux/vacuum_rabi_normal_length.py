"""
A python class describing a T1 measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------
# delete this comment


class vacuumrabinormalLength(Experiment):

    name = "vacuum_rabi_normal_length"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, flux_pulse, fit_fn="exp_decay", **other_params):

        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        self.flux_pulse = flux_pulse
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes

        qubit.play(self.qubit_op)  # play pi qubit pulse
        qua.align(qubit.name, flux.name)  # wait qubit pulse to end
        flux.play(self.flux_pulse, duration=self.y, ampx=-0.138)  #
        qua.align(flux.name, rr.name)  # wait for partial qubit decay
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    y_start = 10#10
    y_stop = 100 #100
    y_step = 2

    x_start = -0.2
    x_stop = -0.1
    x_step = 0.002

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 8000,
        "wait_time": 100000,
        # "x_sweep": ((x_start), (x_stop + x_step / 2), (x_step)),
        "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        "qubit_op": "gaussian_pi",
        "flux_pulse": "constant_pulse",
        "single_shot": False,
        "plot_quad": "I_AVG",
        # "fetch_period": 5,
         
    }

    plot_parameters = {
        "xlabel": "Relaxation time (clock cycles)",
        # "ylabel": "Relaxation time (clock cycles)",
        # "plot_type": "2D",
    }

    experiment = vacuumrabinormalLength(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
