"""
A python class describing a readout resonator spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class RRSpectroscopyFastFlux(Experiment):

    name = "rr_spec_fast_flux"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "fit_fn",  # fit function
        "flux_op",
    }

    def __init__(self, flux_op, rr_delay, qubit_delay, fit_fn=None, **other_params):

        self.fit_fn = fit_fn
        self.flux_op = flux_op
        self.rr_delay = rr_delay
        self.qubit_delay = qubit_delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        (rr, qubit, flux, cav, ) = self.modes  # get the modes

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequenc
        if 1: # normal
            
            # cav.play("const_cohstate_1", ampx=self.y)  # play displacement to cavity
            qubit.play("gaussian_pi", self.y)  # play pi qubit pulse -109e6
            qua.align(qubit.name, flux.name, rr.name)  # align measurement
            flux.play("square_IIR_long", ampx=-0.7)
            qua.wait(int((20) // 4), rr.name)
        if 0: #castle
            flux.play(self.flux_op, ampx=self.y)  # to make off resonance
            qua.wait(int((self.qubit_delay) // 4), qubit.name)  # ns
            # qubit.play(self.qubit_op)  # play pi qubit pulse -109e6
            # qua.align(flux.name, rr.name)
            qua.wait(int((self.rr_delay) // 4), rr.name)
        # first readout
        rr.measure((self.I, self.Q))  # measure qubit state
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        if 0: 
            # second readout
            rr.measure((self.I, self.Q))  # measure qubit state
            if self.single_shot:  # assign state to G or E
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    x_start = -53e6
    x_stop = -47e6
    x_step = 0.05e6

    parameters = {
        "modes": ["RR", "QUBIT", "FLUX", "CAVITY"],
        "reps": 2000,
        "wait_time": 60e3, #1e6,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "y_sweep": (0.0, 1),
        # "plot_quad": "I_AVG",
        "flux_op": "detuned_readout", # square_IIR_superf_readout
        "fit_fn": "gaussian",
        # "single_shot": True,
        "qubit_delay": 200,  # ns
        "rr_delay":600,  # ns
        "fetch_period": 3,
    }

    plot_parameters = {
        "xlabel": "Resonator pulse frequency (Hz)",
        # "skip_plot": True,
    }

    experiment = RRSpectroscopyFastFlux(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
