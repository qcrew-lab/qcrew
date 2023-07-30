"""
A python class describing a vacuum rabi measurement using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qcrew.control import Stagehand
from qcrew.control.pulses.numerical_pulse import NumericalPulse
from qcrew.analyze import fit
from qm import qua

import numpy as np
import h5py

# ---------------------------------- Class -------------------------------------
# delete this comment


class QubitSpectroscopyFFCastleVR(Experiment):

    name = "qubit_spec_ff_castle_vaccum_rabi"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        rr_delay,
        qubit_delay,
        flux_op,
        flux_scaling,
        fit_fn=None,
        **other_params,
    ):
        self.flux_scaling = flux_scaling
        self.flux_op = flux_op
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        self.rr_delay = rr_delay
        self.qubit_delay = qubit_delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        flux.play("castle_IIR_230727_396ns_0dot00", ampx=self.flux_scaling)
        qua.wait(int((450) // 4), rr.name, qubit.name)  # ns
        qubit.play(self.qubit_op)  # play pi qubit pulse -109e6
        qua.wait(int((920) // 4), rr.name)
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)
        qua.align()


class VacuumRabi(Experiment):

    name = "vacuum_rabi_castle"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        flux_len,
        internal_sweep,
        flux_scaling,
        fit_fn="",
        **other_params,
    ):
        self.qubit_op = qubit_op  # pi pulse
        self.fit_fn = fit_fn
        self.flux_len = flux_len
        self.internal_sweep = internal_sweep
        self.flux_scaling = flux_scaling
        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, flux = self.modes  # get the modes
        for flux_amp in self.internal_sweep:
            qua.wait(115, qubit.name)
            qubit.play(self.qubit_op)  # play pi qubit pulse
            if abs(flux_amp) < 1e-3:
                flux_amp = 0
            amp_str = f"{flux_amp:.2f}".replace("-", "m").replace(".", "dot")
            flux.play(f"castle_IIR_230727_{amp_str}", ampx=self.flux_scaling)  # ns
            qua.wait(int((1100 + 24) // 4), rr.name, qubit.name)  # cc
            rr.measure((self.I, self.Q))  # measure qubit state
            if self.single_shot:  # assign state to G or E7
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )
            qua.wait(int(self.wait_time // 4))  # wait system reset
            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    flux_scaling = 0.51
    flux_amp_list = np.arange(-0.16, 0.15, 0.02)
    flux_len_list = np.arange(4, 196, 4)
    
    plot_parameters = {
        "xlabel": "--",
        # "plot_type": "2D",
    }
    parameters_qubit_spec = {
        "modes": ["QUBIT", "RR", "FLUX"],
        "reps": 2000,
        "wait_time": 60e3,
        "x_sweep": (int(-125e6), int(-75e6 + 0.75e6 / 2), int(0.75e6)),
        "qubit_op": "gaussian_pi",
        "qubit_delay": 200,  # ns
        "rr_delay": 700,  # ns
        "flux_op": "constant_pulse",
        "fit_fn": "gaussian",
        "plot_quad": "I_AVG",
        "fetch_period": 2,
        "flux_scaling": flux_scaling,
    }

    check_qubit_freq_period = 1  # check every this number of experiments
    qubit_freq_target = -100.1e6
    correction_coef = 90.53e9
    exp_count = 0
    for flux_len in flux_len_list:
            ## Adjust qubit frequency to the right place
            if exp_count % check_qubit_freq_period == 0:

                ## Do qubit spectroscopy
                experiment = QubitSpectroscopyFFCastleVR(**parameters_qubit_spec)
                experiment.setup_plot(**plot_parameters)
                prof.run(experiment)

                ## Get data
                file = h5py.File(experiment.filename, "r")
                data = file["data"]
                I_AVG = np.array(data["I_AVG"])
                freqs = np.array(data["x"])

                ## Fit data to gaussian
                params = fit.do_fit("gaussian", freqs, I_AVG)
                qubit_freq = float(params["x0"].value)

                ## Calculate adjusted current
                with Stagehand() as stage:
                    yoko = stage.YOKO
                    current_initial = yoko.level
                    current_target = (
                        current_initial + (qubit_freq_target - qubit_freq) / correction_coef
                    )
                    print(current_target)
                    if -0.9e-3 > current_target > -1.3e-3:
                        yoko.ramp(current_target, yoko.level, np.abs(-0.005e-3))

            exp_count += 1

            # with Stagehand() as stage:
            #     flux = stage.FLUX
            #     for amp in flux_amp_list:
            #         if abs(amp) < 1e-3:
            #             amp = 0
            #         amp_str = f"{amp:.2f}".replace("-", "m").replace(".", "dot")
            #         flux.operations = {
            #             f"castle_IIR_230727_{amp_str}": NumericalPulse(
            #                 path=f"C:/Users/qcrew/Desktop/qcrew/qcrew/config/fast_flux_pulse/castle_max/castle_IIR_230727_{flux_len}ns_{amp_str}.npz",
            #                 I_quad="I_quad",
            #                 Q_quad="Q_quad",
            #                 ampx=1,
            #             ),
            #         }

            # parameters = {
            #     "modes": ["QUBIT", "RR", "FLUX"],
            #     "reps": 8000,
            #     "wait_time": 1.25e6,
            #     "qubit_op": "gaussian_pi",
            #     # "single_shot": True,
            #     "plot_quad": "I_AVG",
            #     "fetch_period": 20,
            #     "flux_len": flux_len,
            #     "internal_sweep": flux_amp_list,
            #     "flux_scaling": flux_scaling,
            # }

            # experiment = VacuumRabi(**parameters)
            # experiment.setup_plot(**plot_parameters)
            # prof.run(experiment)
