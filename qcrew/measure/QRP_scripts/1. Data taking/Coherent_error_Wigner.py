"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua
import numpy as np


# ---------------------------------- Class -------------------------------------
class CohErrWigner(Experiment):
    name = "Coherent_error_Wigner"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
        "delay",
    }

    def __init__(
        self,
        qubit_op,
        cav_op,
        cav_grape,
        qubit_grape,
        delay,
        fit_fn=None,
        **other_params
    ):
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.cav_grape = cav_grape
        self.qubit_grape = qubit_grape
        self.fit_fn = fit_fn
        self.delay = delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.update_frequency(qubit.name, qubit.int_freq)
        
        # the 1st selection
        rr.measure((self.I, self.Q))
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        
        qua.align()
        qua.wait(250)
        qua.align()
        
        # STATE PREPARATION
        if self.cav_grape == "vacuum":
            pass
        elif self.cav_grape == "coh1":
            cav.play(
                self.cav_op,
                ampx=(1, 0, 0, 1),
                phase=-0.25,
            )
        else:
            qubit.play(self.qubit_grape)
            cav.play(self.cav_grape)

        qua.align(cav.name, qubit.name)

        # WIGNER
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4), cav.name, qubit.name
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op, phase=self.y)  # play pi/2 pulse around X
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
    
        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__": 
    pulses = [
        "vacuum",
        "grape_fock1",
        "grape_fock2",
        "grape_fock3",
        "grape_fock4",
        "grape_fock5",
    ]

    x_start = 1
    x_stop = 6
    x_step = 1


    for pulse in pulses:
            parameters = {
                "modes": ["QUBIT", "CAV", "RR"],
                "reps": 200,
                "wait_time": 16e6,
                "delay": 289,
                "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
                "y_sweep": [0.0, 0.5],
                "qubit_op": "qubit_gaussian_48ns_pi2_pulse",
                "cav_op": "coherent_1_long",
                # "plot_quad": "I_AVG",
                "single_shot": True,
                "fetch_period": 4,
                "qubit_grape": pulse,
                "cav_grape": pulse,
            }

            plot_parameters = {
                "xlabel": "Qubit pulse frequency (Hz)",
                "plot_err": None,
            }

            experiment = CohErrWigner(**parameters)
            experiment.name = (
                "Coherent_Error_Wigner"
                + str(pulse)
            )
            experiment.setup_plot(**plot_parameters)

            prof.run(experiment)
