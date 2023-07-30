"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class QubitSpectroscopyFastFlux(Experiment):

    name = "number_splitting_ff"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, rr_delay, qubit_delay, flux_op, qubit_op_measure, fit_fn=None, **other_params
    ):

        self.flux_op = flux_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.rr_delay = rr_delay
        self.qubit_delay = qubit_delay
        self.qubit_op_measure=qubit_op_measure

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux, cav = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        if 1:  # castle predistorted
            flux.play(
                "castle_IIR_230727_76", ampx=0.574
            )  # to make off resonance
            qua.wait(int((250) // 4), rr.name, qubit.name)  # ns
            qubit.play(self.qubit_op, amp=self.y) 
            qua.wait(int((250) // 4), rr.name, qubit.name)
        
  
        # number splitting
        qua.update_frequency(qubit.name, self.x)
        qubit.play(self.qubit_op_measure)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -110e6  # -100e6
    x_stop = -90e6  # -40e6
    x_step = 0.25e6

    parameters = {
        "modes": ["QUBIT", "RR", "FLUX", "CAVITY"],
        "reps": 10000,
        "wait_time": 60e3,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": [
            0,1,
        ],
        "qubit_op": "gaussian_pi",
        "qubit_delay": 200,  # ns
        "rr_delay": 700,  # ns
        "flux_op": "constant_pulse",
        "fit_fn": "gaussian",
        "qubit_op_measure": "gaussian_pi_280",
        # "single_shot": True,
        "plot_quad": "I_AVG",
        "fetch_period": 2,
    }

    plot_parameters = {
        "xlabel": "Qubit pulse frequency (Hz)",
    }

    experiment = QubitSpectroscopyFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
