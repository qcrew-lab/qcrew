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

    name = "qubit_spec_fast_flux"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        # self.sweep_parameters = [
        #     (0.0, -50.2e6),
        #     (0.1, -50.2e6),
        #     (0.3, -50.3e6),
            # (0.5, -50.4e6),
            # (0.6, -50.6e6),
            # (0.8, -50.7e6),
            # (1.0, -50.7e6),
            #(1.5, -51.0e6),
        
        # self.internal_sweep = [
        #     "0.0, -50.2e6",
        #     "0.1, -50.2e6",
        #     "0.3, -50.3e6",
            # "0.5, -50.4e6",
            # "0.6, -50.6e6",
            # "0.8, -50.7e6",
            # "1.0, -50.7e6",
            #"1.5, -51.0e6",
        # ]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, flux, rr = self.modes  # get the modes
        # for params in self.sweep_parameters:
        #     flux_ampx, rr_freq = params
        #     qua.align()
        #     qua.update_frequency(rr.name, int(rr_freq))
        #qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qua.wait(self.y, qubit.name)
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.wait(100, flux.name)
        flux.play("constant_pulse", ampx=self.x)
        qua.wait(200, rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), flux.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    y_start = 60  # 181.25e6
    y_stop = 160  # 181.5e6
    y_step = 1
    
    x_start = 0.01  # 181.25e6
    x_stop = 0.3  # 181.5e6
    x_step = 0.01


    parameters = {
        "modes": ["QUBIT", "FLUX", "RR"],
        "reps": 500000,
        "wait_time": 20000,
        "y_sweep": (int(y_start), int(y_stop + y_step / 2), int(y_step)),
        "x_sweep": ((x_start), (x_stop + x_step / 2), (x_step)),
        "qubit_op": "constant_pi_pulse",
        #"plot_quad": "I_AVG",
    }

    plot_parameters = {
        "xlabel": "flux pulse amp",
        "plot_type": "2D"
    }

    experiment = QubitSpectroscopyFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
