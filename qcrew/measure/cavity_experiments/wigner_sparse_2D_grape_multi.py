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


class wignerSparse(Experiment):
    name = "wigner_sparse"

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
        cav_amp,
        delay,
        point,
        fit_fn=None,
        **other_params
    ):
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.cav_grape = cav_grape
        self.qubit_grape = qubit_grape
        self.cav_amp = cav_amp
        self.fit_fn = fit_fn
        self.point = point
        self.delay = delay

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, qubit.int_freq)
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

        qua.align()

        cav.play(
            self.cav_op,
            ampx=self.point,
            phase=0.25,
        )
        qua.align()
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.wait(
            int(self.delay // 4),
            cav.name,
            qubit.name,
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op)  # play pi/2 pulse around X

        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal

        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    pulselist = [
        "vacuum",
        "grape_fock1_pulse",
        "grape_fock2_pulse",
        "grape_fock3_pulse",
        "grape_fock01_pulse",
        "grape_fock0i1_pulse",
        "grape_fock02_pulse",
        "grape_fock0i2_pulse",
        "grape_fock03_pulse",
        "grape_fock0i3_pulse",
        "grape_fock12_pulse",
        "grape_fock1i2_pulse",
        "grape_fock13_pulse",
        "grape_fock1i3_pulse",
        "grape_fock23_pulse",
        "grape_fock2i3_pulse",
        "coh1",
    ]

    pointlist = [
        # [0.0, 0.0, 0.0, 0.0],
        [-0.64814162, -0.36008861, 0.36008861, -0.64814162],
        [-0.00490393, 0.26529024, -0.26529024, -0.00490393],
        [-0.02240402, 0.74343831, -0.74343831, -0.02240402],
        [-0.53720059, 1.03749518, -1.03749518, -0.53720059],
        [-0.60380164, -1.0046089, 1.0046089, -0.60380164],
        [0.59025967, 1.01336611, -1.01336611, 0.59025967],
        [0.60430717, -1.01099343, 1.01099343, 0.60430717],
        [0.64472497, -0.37598059, 0.37598059, 0.64472497],
        [0.23570834, -0.1320831, 0.1320831, 0.23570834],
        [-0.59650228, 0.35521383, -0.35521383, -0.59650228],
        [-0.0128941, -0.7098708, 0.7098708, -0.0128941],
        [0.59471572, 0.3513811, -0.3513811, 0.59471572],
        [1.17389003, -0.04054449, 0.04054449, 1.17389003],
        [-1.16925829, -0.01832806, 0.01832806, -1.16925829],
        [-0.22871322, -0.13728926, 0.13728926, -0.22871322],
    ]

    x_start = 30e6
    x_stop = 150e6
    x_step = 30e6

    # freq_points = np.concatenate(
    #     np.linspace(177.2e6, 177.6e6, 0.005e6)
    # )

    for pulse in pulselist:
        for i in range(len(pointlist)):
            parameters = {
                "modes": ["QUBIT", "CAV", "RR"],
                "reps": 30,
                "wait_time": 7e6,
                "delay": 289,
                "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
                "qubit_op": "qubit_gaussian_short_pi2_pulse",
                "cav_op": "coherent_1_long",
                "cav_amp": 0,
                # "plot_quad": "I_AVG",
                "single_shot": True,
                "fetch_period": 2,
                "qubit_grape": pulse,
                "cav_grape": pulse,
                "point": pointlist[i],
            }

            plot_parameters = {"xlabel": "Qubit pulse frequency (Hz)", "plot_err": None}

            experiment = wignerSparse(**parameters)

            experiment.name = (
                "QML_number_split_spec_"
                + pulse
                + "_point{}".format(i + 1)
                # "QML_number_split_spec_" + pulse + "_no_displacement"
            )

            experiment.setup_plot(**plot_parameters)

            prof.run(experiment)
