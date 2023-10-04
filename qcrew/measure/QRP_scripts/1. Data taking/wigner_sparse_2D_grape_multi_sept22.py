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

        # WIGNER DISPLACEMENT
        cav.play(
            self.cav_op,
            ampx=self.point,
            phase=0.25,
        )
        qua.align()

        # RAMSEY
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

    pulselistD6 = pulselistD6 = [
        "vacuum",
        "coh1",
        "grape_fock1",
        "grape_fock2",
        "grape_fock3",
        "grape_fock4",
        # 'fock5',
        "grape_fock01",
        "grape_fock0i1",
        "grape_fock02",
        "grape_fock0i2",
        "grape_fock03",
        "grape_fock0i3",
        "grape_fock04",
        "grape_fock0i4",
        "grape_fock05",
        "grape_fock0i5",
        "grape_fock12",
        "grape_fock1i2",
        "grape_fock13",
        "grape_fock1i3",
        "grape_fock14",
        "grape_fock1i4",
        "grape_fock15",
        "grape_fock1i5",
        "grape_fock23",
        "grape_fock2i3",
        "grape_fock24",
        "grape_fock2i4",
        "grape_fock25",
        "grape_fock2i5",
        "grape_fock34",
        "grape_fock3i4",
        "grape_fock35",
        "grape_fock3i5",
        "grape_fock45",
        # 'fock4i5',
    ]

    listofpulselists = [pulselistD6]

    # pointlistD2 = [
    #     [0.23670853, 0.36735822, -0.36735822, 0.23670853],
    #     [0.19978692, -0.38867497, 0.38867497, 0.19978692],
    #     [-0.43649562, 0.02131684, -0.02131684, -0.43649562],
    # ]

    # pointlistD3 = [
    #     [-0.78150288, -0.16616467, 0.16616467, -0.78150288],
    #     [-0.40824996, 0.71347646, -0.71347646, -0.40824996],
    #     [-0.19705357, 0.21071451, -0.21071451, -0.19705357],
    #     [0.28346722, 0.08297085, -0.08297085, 0.28346722],
    #     [-0.06291041, -0.28848442, 0.28848442, -0.06291041],
    #     [0.75821827, -0.35737599, 0.35737599, 0.75821827],
    #     [0.60283096, 0.55035922, -0.55035922, 0.60283096],
    #     [-0.0850512, -0.830472, 0.830472, -0.0850512],
    # ]

    # pointlistD4 = [
    #     [-0.64814162, -0.36008861, 0.36008861, -0.64814162],
    #     [-0.00490393, 0.26529024, -0.26529024, -0.00490393],
    #     [-0.02240402, 0.74343831, -0.74343831, -0.02240402],
    #     [-0.53720059, 1.03749518, -1.03749518, -0.53720059],
    #     [-0.60380164, -1.0046089, 1.0046089, -0.60380164],
    #     [0.59025967, 1.01336611, -1.01336611, 0.59025967],
    #     [0.60430717, -1.01099343, 1.01099343, 0.60430717],
    #     [0.64472497, -0.37598059, 0.37598059, 0.64472497],
    #     [0.23570834, -0.1320831, 0.1320831, 0.23570834],
    #     [-0.59650228, 0.35521383, -0.35521383, -0.59650228],
    #     [-0.0128941, -0.7098708, 0.7098708, -0.0128941],
    #     [0.59471572, 0.3513811, -0.3513811, 0.59471572],
    #     [1.17389003, -0.04054449, 0.04054449, 1.17389003],
    #     [-1.16925829, -0.01832806, 0.01832806, -1.16925829],
    #     [-0.22871322, -0.13728926, 0.13728926, -0.22871322],
    # ]

    # pointlistD5 = [
    #     [-1.40158538, -0.36375925, 0.36375925, -1.40158538],
    #     [-0.217802425, -0.0446111, 0.0446111, -0.217802425],
    #     [-0.258509099, -0.55853673, 0.55853673, -0.258509099],
    #     [-0.654056674, -0.14691191, 0.14691191, -0.654056674],
    #     [1.207598, 0.82312899, -0.82312899, 1.207598],
    #     [0.768437437, -0.69813826, 0.69813826, 0.768437437],
    #     [-0.537183525, 0.38486941, -0.38486941, -0.537183525],
    #     [-0.000669003284, 1.46974125, -1.46974125, -0.000669003284],
    #     [0.0786731177, 0.18690824, -0.18690824, 0.0786731177],
    #     [0.0416505231, 0.67026276, -0.67026276, 0.0416505231],
    #     [-1.01557524, 0.19185523, -0.19185523, -1.01557524],
    #     [-1.19439104, 0.82312854, -0.82312854, -1.19439104],
    #     [0.123124767, -0.18302953, 0.18302953, 0.123124767],
    #     [1.37620023, -0.47227803, 0.47227803, 1.37620023],
    #     [-0.818519778, -0.64372027, 0.64372027, -0.818519778],
    #     [0.641520025, -0.18797968, 0.18797968, 0.641520025],
    #     [-0.0647909631, -1.03962092, 1.03962092, -0.0647909631],
    #     [0.541178684, -1.34821744, 1.34821744, 0.541178684],
    #     [0.324192355, -0.58950634, 0.58950634, 0.324192355],
    #     [-0.704142445, -1.29464113, 1.29464113, -0.704142445],
    #     [0.498089059, 0.92112831, -0.92112831, 0.498089059],
    #     [0.510167997, 0.43435832, -0.43435832, 0.510167997],
    #     [-0.459644335, 0.92447127, -0.92447127, -0.459644335],
    #     [1.02888822, 0.14967752, -0.14967752, 1.02888822],
    # ]

    pointlistD6 = [
        [-0.7208703, 0.60408255, -0.60408255, -0.7208703],
        [1.36027267, -0.99846325, 0.99846325, 1.36027267],
        [0.68815669, 0.6389587, -0.6389587, 0.68815669],
        [-1.05601011, 0.77237077, -0.77237077, -1.05601011],
        [0.20002496, 0.0811553, -0.0811553, 0.20002496],
        [-0.67976216, -1.10072435, 1.10072435, -0.67976216],
        [-0.16295851, 0.10618929, -0.10618929, -0.16295851],
        [0.37545067, 1.18004172, -1.18004172, 0.37545067],
        [1.25285936, 0.14918359, -0.14918359, 1.25285936],
        [-0.40493073, -0.44070757, 0.44070757, -0.40493073],
        [-0.59303321, 0.09517527, -0.09517527, -0.59303321],
        [-0.86564916, -0.35630909, 0.35630909, -0.86564916],
        [-0.90112497, 1.4380865, -1.4380865, -0.90112497],
        [1.60864274, 0.48330144, -0.48330144, 1.60864274],
        [0.92768843, -0.17975043, 0.17975043, 0.92768843],
        [-0.99225357, 0.1795986, -0.1795986, -0.99225357],
        [0.44665373, -0.2792634, 0.2792634, 0.44665373],
        [1.0110178, 0.8157254, -0.8157254, 1.0110178],
        [0.00899513, -1.22170064, 1.22170064, 0.00899513],
        [0.43859161, -0.84307385, 0.84307385, 0.43859161],
        [0.69271776, -1.10881517, 1.10881517, 0.69271776],
        [0.05354922, -1.6820833, 1.6820833, 0.05354922],
        [-1.2977396, -1.11942467, 1.11942467, -1.2977396],
        [0.57672469, 0.17628488, -0.17628488, 0.57672469],
        [0.02026275, -0.21008509, 0.21008509, 0.02026275],
        [0.05025944, -0.58211451, 0.58211451, 0.05025944],
        [-0.0845683, 0.91942211, -0.91942211, -0.0845683],
        [-1.67370691, 0.23131353, -0.23131353, -1.67370691],
        [1.15249033, -0.5483415, 0.5483415, 1.15249033],
        [-0.3215939, 1.23910642, -1.23910642, -0.3215939],
        [0.60130374, 1.57779297, -1.57779297, 0.60130374],
        [-0.36575621, -0.86851137, 0.86851137, -0.36575621],
        [0.2864474, 0.52782501, -0.52782501, 0.2864474],
        [-0.28337477, 0.52318056, -0.52318056, -0.28337477],
        [-1.28155538, -0.34082969, 0.34082969, -1.28155538],
    ]

    listofpointlists = [pointlistD6]

    x_start = 1
    x_stop = 6
    x_step = 1

    for dim in range(1):
        pulselist = listofpulselists[0]
        pointlist = listofpointlists[0]

        for pulse in pulselist:
            for point in range(len(pointlist)):
                parameters = {
                    "modes": ["QUBIT", "CAV", "RR"],
                    "reps": 200,
                    "wait_time": 16e6,
                    "delay": 289,
                    "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
                    "y_sweep": [0.0, 0.5],
                    "qubit_op": "qubit_gaussian_64ns_pi2_pulse",
                    "cav_op": "coherent_1_long",
                    "cav_amp": 0,
                    # "plot_quad": "I_AVG",
                    "single_shot": True,
                    "fetch_period": 4,
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
                    + str(6)
                    + "_"
                    + str(pulse)
                    + "_point{}".format(point + 1)
                )
                experiment.setup_plot(**plot_parameters)

                prof.run(experiment)
