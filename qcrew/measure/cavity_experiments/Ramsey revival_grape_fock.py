"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua

# ---------------------------------- Class -------------------------------------


class Ramseyrevival(Experiment):
    name = "Ramsey_revival"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, cav_op, cavity_amp, qubit_grape,cav_grape,  fit_fn=None, **other_params):
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.cavity_amp = cavity_amp
        self.fit_fn = fit_fn
        self.qubit_grape = qubit_grape
        self.cav_grape = cav_grape
        super().__init__(**other_params)  # Passes other parameters to parent


    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq)
        
        qubit.play(self.qubit_grape)
        cav.play(self.cav_grape)
        qua.align(cav.name, qubit.name)

        qua.update_frequency(qubit.name, 174.69e6)
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.wait(self.x, qubit.name)
        qubit.play(self.qubit_op)  # play  qubit pulse with pi/2
        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    # x_start = 4
    # x_stop = 600
    # x_step = 5
    x_start = 4
    x_stop = 200
    x_step = 1
    parameters = {
        "modes": ["QUBIT", "CAV", "RR"],
        "reps": 200,
        "wait_time": 10e6,
        "cavity_amp": 1.9,
        "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
        "qubit_op": "qubit_gaussian_short_pi2_pulse",
        "cav_op": "coherent_1",
        "qubit_grape": "grape_fock1_pulse",
        "cav_grape": "grape_fock1_pulse",
        # "plot_quad": "I_AVG",
        "fit_fn": 'gaussian',
        "fetch_period": 2,
        "single_shot" : True,
    }

    plot_parameters = {
        "xlabel": "Wait time (clock)",
        "plot_err": False,

    }

    experiment = Ramseyrevival(**parameters)
    experiment.setup_plot(**plot_parameters)

    prof.run(experiment)
