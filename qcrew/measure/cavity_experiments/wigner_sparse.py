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

        qua.reset_frame(cav.name)
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
            int(self.delay // 4), cav.name, qubit.name
        )  # conditional phase gate on even, odd Fock state
        qubit.play(self.qubit_op)  # play pi/2 pulse around X
        qua.align(qubit.name, rr.name)  # align measurement
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        # wait system reset
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    pulselistD2 = [
        "vacuum",
        "grape_fock1_pulse",
        "grape_fock01_pulse",
        "grape_fock0i1_pulse",
        "coh1",
    ]

    pulselistD3 = [
        "vacuum",
        "grape_fock1_pulse",
        "grape_fock2_pulse",
        "grape_fock01_pulse",
        "grape_fock0i1_pulse",
        "grape_fock02_pulse",
        "grape_fock0i2_pulse",
        "grape_fock12_pulse",
        "grape_fock1i2_pulse",
        "coh1",
    ]

    pulselistD4 = [
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

    pulselistD5 = [
        "vacuum",
        "grape_fock1_pulse",
        "grape_fock2_pulse",
        "grape_fock3_pulse",
        "grape_fock4_pulse",
        "grape_fock01_pulse",
        "grape_fock0i1_pulse",
        "grape_fock02_pulse",
        "grape_fock0i2_pulse",
        "grape_fock03_pulse",
        "grape_fock0i3_pulse",
        "grape_fock04_pulse",
        "grape_fock0i4_pulse",
        "grape_fock12_pulse",
        "grape_fock1i2_pulse",
        "grape_fock13_pulse",
        "grape_fock1i3_pulse",
        "grape_fock14_pulse",
        "grape_fock1i4_pulse",
        "grape_fock23_pulse",
        "grape_fock2i3_pulse",
        "grape_fock24_pulse",
        "grape_fock2i4_pulse",
        "grape_fock34_pulse",
        "grape_fock3i4_pulse",
        "coh1",
    ]

    pulselistD6 = [
        "vacuum",
        "grape_fock1_pulse",
        "grape_fock2_pulse",
        "grape_fock3_pulse",
        "grape_fock4_pulse",
        "grape_fock5_pulse",
        "grape_fock01_pulse",
        "grape_fock0i1_pulse",
        "grape_fock02_pulse",
        "grape_fock0i2_pulse",
        "grape_fock03_pulse",
        "grape_fock0i3_pulse",
        "grape_fock04_pulse",
        "grape_fock0i4_pulse",
        "grape_fock05_pulse",
        "grape_fock0i5_pulse",
        "grape_fock12_pulse",
        "grape_fock1i2_pulse",
        "grape_fock13_pulse",
        "grape_fock1i3_pulse",
        "grape_fock14_pulse",
        "grape_fock1i4_pulse",
        "grape_fock15_pulse",
        "grape_fock1i5_pulse",
        "grape_fock23_pulse",
        "grape_fock2i3_pulse",
        "grape_fock24_pulse",
        "grape_fock2i4_pulse",
        "grape_fock25_pulse",
        "grape_fock2i5_pulse",
        "grape_fock34_pulse",
        "grape_fock3i4_pulse",
        "grape_fock35_pulse",
        "grape_fock3i5_pulse",
        "grape_fock45_pulse",
        "grape_fock4i5_pulse",
        "coh1",
    ]

    listofpulselists = [pulselistD6, pulselistD5, pulselistD4, pulselistD3, pulselistD2]

    pointlistD2 = [
        [0.23670853, 0.36735822, -0.36735822, 0.23670853],
        [0.19978692, -0.38867497, 0.38867497, 0.19978692],
        [-0.43649562, 0.02131684, -0.02131684, -0.43649562],
    ]

    pointlistD3 = [
        [-0.78150288, -0.16616467, 0.16616467, -0.78150288],
        [-0.40824996, 0.71347646, -0.71347646, -0.40824996],
        [-0.19705357, 0.21071451, -0.21071451, -0.19705357],
        [0.28346722, 0.08297085, -0.08297085, 0.28346722],
        [-0.06291041, -0.28848442, 0.28848442, -0.06291041],
        [0.75821827, -0.35737599, 0.35737599, 0.75821827],
        [0.60283096, 0.55035922, -0.55035922, 0.60283096],
        [-0.0850512, -0.830472, 0.830472, -0.0850512],
    ]

    pointlistD4 = [
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

    pointlistD5 = [
        [-1.40158538, -0.36375925, 0.36375925, -1.40158538],
        [-0.217802425, -0.0446111, 0.0446111, -0.217802425],
        [-0.258509099, -0.55853673, 0.55853673, -0.258509099],
        [-0.654056674, -0.14691191, 0.14691191, -0.654056674],
        [1.207598, 0.82312899, -0.82312899, 1.207598],
        [0.768437437, -0.69813826, 0.69813826, 0.768437437],
        [-0.537183525, 0.38486941, -0.38486941, -0.537183525],
        [-0.000669003284, 1.46974125, -1.46974125, -0.000669003284],
        [0.0786731177, 0.18690824, -0.18690824, 0.0786731177],
        [0.0416505231, 0.67026276, -0.67026276, 0.0416505231],
        [-1.01557524, 0.19185523, -0.19185523, -1.01557524],
        [-1.19439104, 0.82312854, -0.82312854, -1.19439104],
        [0.123124767, -0.18302953, 0.18302953, 0.123124767],
        [1.37620023, -0.47227803, 0.47227803, 1.37620023],
        [-0.818519778, -0.64372027, 0.64372027, -0.818519778],
        [0.641520025, -0.18797968, 0.18797968, 0.641520025],
        [-0.0647909631, -1.03962092, 1.03962092, -0.0647909631],
        [0.541178684, -1.34821744, 1.34821744, 0.541178684],
        [0.324192355, -0.58950634, 0.58950634, 0.324192355],
        [-0.704142445, -1.29464113, 1.29464113, -0.704142445],
        [0.498089059, 0.92112831, -0.92112831, 0.498089059],
        [0.510167997, 0.43435832, -0.43435832, 0.510167997],
        [-0.459644335, 0.92447127, -0.92447127, -0.459644335],
        [1.02888822, 0.14967752, -0.14967752, 1.02888822],
    ]

    pointlistD6 = [
        [-1.71596569, 0.2716384, -0.2716384, -1.71596569],
        [1.43327279, 0.92379476, -0.92379476, 1.43327279],
        [0.284933, 0.56312997, -0.56312997, 0.284933],
        [-0.58285904, 0.72029026, -0.72029026, -0.58285904],
        [0.15814667, -0.5508669, 0.5508669, 0.15814667],
        [-0.1716369, 0.58090801, -0.58090801, -0.1716369],
        [0.768172, 1.05042267, -1.05042267, 0.768172],
        [-0.24288805, -1.70266141, 1.70266141, -0.24288805],
        [1.07583557, -1.27776826, 1.27776826, 1.07583557],
        [0.64162878, -0.72429249, 0.72429249, 0.64162878],
        [-0.33864416, -0.45468057, 0.45468057, -0.33864416],
        [-1.12178907, 0.68929671, -0.68929671, -1.12178907],
        [-0.58229989, -1.16082215, 1.16082215, -0.58229989],
        [-1.29011731, -1.04706078, 1.04706078, -1.29011731],
        [0.5296398, -0.25299632, 0.25299632, 0.5296398],
        [0.26795992, 1.68223039, -1.68223039, 0.26795992],
        [-0.13863234, -0.877622, 0.877622, -0.13863234],
        [-0.79405464, -0.56780848, 0.56780848, -0.79405464],
        [-0.92144364, 0.2455748, -0.2455748, -0.92144364],
        [0.09324319, 0.98815899, -0.98815899, 0.09324319],
        [0.02723585, 0.2447772, -0.2447772, 0.02723585],
        [-0.44932904, 0.28264761, -0.28264761, -0.44932904],
        [-0.2861437, 1.28207382, -1.28207382, -0.2861437],
        [1.277238, 0.26841395, -0.26841395, 1.277238],
        [-1.27451241, -0.32007509, 0.32007509, -1.27451241],
        [-0.88710808, 1.47741765, -1.47741765, -0.88710808],
        [0.45921965, 0.20072382, -0.20072382, 0.45921965],
        [1.00090878, -0.13464987, 0.13464987, 1.00090878],
        [1.1297064, -0.68674987, 0.68674987, 1.1297064],
        [0.17448967, -0.07387287, 0.07387287, 0.17448967],
        [-0.20092326, -0.02778535, 0.02778535, -0.20092326],
        [0.75147127, 0.51942542, -0.51942542, 0.75147127],
        [1.66397153, -0.3408992, 0.3408992, 1.66397153],
        [-0.60374087, -0.12691263, 0.12691263, -0.60374087],
        [0.31406689, -1.2416499, 1.2416499, 0.31406689],
    ]

    listofpointlists = [pointlistD6, pointlistD5, pointlistD4, pointlistD3, pointlistD2]

    x_start = 1
    x_stop = 6
    x_step = 1

    for i in range(len(listofpulselists)):
        pulselist = listofpulselists[i]
        pointlist = listofpointlists[i]

        for pulse in pulselist:
            for point in range(len(pointlist)):
                parameters = {
                    "modes": ["QUBIT", "CAV", "RR"],
                    "reps": 100,
                    "wait_time": 10e6,
                    "delay": 289,
                    "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
                    "qubit_op": "qubit_gaussian_short_pi2_pulse",
                    "cav_op": "coherent_1_long",
                    "cav_amp": 0,
                    # "plot_quad": "I_AVG",
                    "single_shot": True,
                    "fetch_period": 1,
                    "qubit_grape": pulse,
                    "cav_grape": pulse,
                    "point": pointlist[point],
                }

                plot_parameters = {
                    "xlabel": "Qubit pulse frequency (Hz)",
                    "plot_err": None,
                }

                experiment = wignerSparse(**parameters)
                experiment.name = (
                    "QML_sparse_wigner_D="
                    + str(6-i)
                    + "_"
                    + str(pulse)
                    + "_point{}".format(point + 1)
                )
                experiment.setup_plot(**plot_parameters)

                prof.run(experiment)
