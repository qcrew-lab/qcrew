"""
A python class describing a photon-number split spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""
from typing import ClassVar
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qm import qua


# ---------------------------------- Class -------------------------------------
class NSplitSpectroscopy(Experiment):
    name = "number_split_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self, qubit_op, cav_op, cav_grape, qubit_grape, cav_amp, fit_fn, **other_params
    ):
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.cav_grape = cav_grape
        self.qubit_grape = qubit_grape
        self.cav_amp = cav_amp
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.reset_frame(cav.name)
        qua.update_frequency(qubit.name, qubit.int_freq)

        if self.cav_grape == "vacuum":
            pass
        elif self.cav_grape == "coh1":
            cav.play(self.cav_op, ampx=(1, 0, 0, 1), phase=-0.25)
        else:
            qubit.play(self.qubit_grape)
            cav.play(self.cav_grape)

        # qua.align()
        # cav.play(self.cav_op, ampx=self.cav_amp, phase = -0.25)  # prepare cavity state
        qua.align(cav.name, qubit.name)  # align modes
        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
            )
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    x_start = -67.4e6
    x_stop = -66.4e6
    x_step = 0.01e6

    fock_pulses = [
        # "coh1",
        # "vacuum",
        # "grape_fock1",
        # "grape_fock2",
        # "grape_fock3",
        # "grape_fock4",
        "grape_fock5",
        # "grape_fock6_pulse",
        # "grape_fock7_pulse",
        # "grape_fock8_pulse",
    ]

    for fock in fock_pulses:
        parameters = {
            "modes": ["QUBIT", "CAV", "RR"],
            "reps": 300,
            "wait_time": 12e6,
            "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
            "qubit_op": "qubit_gaussian_sig800ns_pi_pulse",
            "cav_op": "coherent_1_long",
            "cav_amp": 1,
            # "plot_quad": "I_AVG",
            "single_shot": "True",
            "fit_fn": "gaussian",
            "fetch_period": 1,
            "qubit_grape": fock,
            "cav_grape": fock,
        }

        plot_parameters = {"xlabel": "Qubit pulse frequency (Hz)", "plot_err": None}

        experiment = NSplitSpectroscopy(**parameters)
        experiment.setup_plot(**plot_parameters)

        prof.run(experiment)
