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
class NSplitSpectroscopy(Experiment):
    name = "number_split_spec_grape"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        cav_op,
        cav_grape,
        qubit_grape,
        cav_amp,
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

        qua.align()
        cav.play(self.cav_op, ampx=self.point, phase=-0.25)
        qua.align()
        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
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

    pulselistD2 = [
        "vacuum",
        "grape_fock1_pulse",
        "grape_fock01_pulse",
        "grape_fock0i1_pulse",
        "coh1",
    ]

    listofpulselists = [pulselistD6, pulselistD5, pulselistD4, pulselistD3, pulselistD2]

    pointlistD6 = [
        [-0.85703772, -0.41103671, 0.41103671, -0.85703772],
        [0.73225389, -0.96982265, 0.96982265, 0.73225389],
        [-0.21834647, 0.34849838, -0.34849838, -0.21834647],
        [-1.58388171, 0.10675561, -0.10675561, -1.58388171],
        [-0.22752489, -0.98946425, 0.98946425, -0.22752489],
        [0.30810916, 1.35605743, -1.35605743, 0.30810916],
        [0.38449679, -0.01448902, 0.01448902, 0.38449679],
        [-0.44457373, -1.27659996, 1.27659996, -0.44457373],
        [-0.65445865, 1.14111546, -1.14111546, -0.65445865],
        [0.68337999, 0.54264186, -0.54264186, 0.68337999],
        [1.65072948, -0.58656416, 0.58656416, 1.65072948],
        [1.15339348, -1.04776075, 1.04776075, 1.15339348],
        [-1.46868592, -0.83841492, 0.83841492, -1.46868592],
        [-1.40366236, 0.85371123, -0.85371123, -1.40366236],
        [-1.47560326, -1.42267674, 1.42267674, -1.47560326],
        [-0.23425394, -0.59579021, 0.59579021, -0.23425394],
        [-0.04762233, -0.37541208, 0.37541208, -0.04762233],
        [-0.07400758, 0.77805875, -0.77805875, -0.07400758],
        [-0.14728009, -2.30294012, 2.30294012, -0.14728009],
        [-0.6559489, -1.55382849, 1.55382849, -0.6559489],
        [0.99241771, -0.10471466, 0.10471466, 0.99241771],
        [-1.02881791, 0.54348621, -0.54348621, -1.02881791],
        [1.23896643, 0.09430688, -0.09430688, 1.23896643],
        [-0.59414584, 0.23776207, -0.23776207, -0.59414584],
        [1.72710934, 0.58854817, -0.58854817, 1.72710934],
        [-1.04325339, -0.61871112, 0.61871112, -1.04325339],
        [-1.54134671, 1.48896059, -1.48896059, -1.54134671],
        [0.81723316, -1.89940617, 1.89940617, 0.81723316],
        [0.51779053, -0.8204179, 0.8204179, 0.51779053],
        [-2.01598037, -0.10784227, 0.10784227, -2.01598037],
        [-1.51330818, -1.98816387, 1.98816387, -1.51330818],
        [-0.59696256, 1.67346801, -1.67346801, -0.59696256],
        [0.58965213, -0.08301175, 0.08301175, 0.58965213],
        [0.54737316, -1.62678537, 1.62678537, 0.54737316],
        [0.85286478, 0.93814954, -0.93814954, 0.85286478],
    ]

    pointlistD5 = [
        [-1.1848571, 0.8096053, -0.8096053, -1.1848571],
        [-1.00933408, -0.345056, 0.345056, -1.00933408],
        [-1.52223563, -0.04413064, 0.04413064, -1.52223563],
        [0.75142788, -0.23834468, 0.23834468, 0.75142788],
        [1.4343226, 0.78057228, -0.78057228, 1.4343226],
        [0.62963919, 0.40864702, -0.40864702, 0.62963919],
        [-0.27088106, -1.04416493, 1.04416493, -0.27088106],
        [0.51992756, 0.30268825, -0.30268825, 0.51992756],
        [-0.12314268, 1.327761, -1.327761, -0.12314268],
        [1.49149501, -0.11959137, 0.11959137, 1.49149501],
        [-0.48826335, 0.48197647, -0.48197647, -0.48826335],
        [-0.59888712, -1.37432475, 1.37432475, -0.59888712],
        [-1.13485624, 1.14524419, -1.14524419, -1.13485624],
        [-0.90709117, -0.35785598, 0.35785598, -0.90709117],
        [0.11325643, 0.94850705, -0.94850705, 0.11325643],
        [1.03258476, 0.91627408, -0.91627408, 1.03258476],
        [-0.32048601, 1.7938981, -1.7938981, -0.32048601],
        [-0.31784596, 0.26316093, -0.26316093, -0.31784596],
        [-0.35660681, -0.55927563, 0.55927563, -0.35660681],
        [0.61724267, 1.65008629, -1.65008629, 0.61724267],
        [0.59088513, -1.02627816, 1.02627816, 0.59088513],
        [0.28546229, 0.28482724, -0.28482724, 0.28546229],
        [0.33134764, -0.73575301, 0.73575301, 0.33134764],
        [0.26215286, -0.25804249, 0.25804249, 0.26215286],
    ]

    pointlistD4 = [
        [0.38225617, -0.99489863, 0.99489863, 0.38225617],
        [-1.11579993, -0.00203959, 0.00203959, -1.11579993],
        [0.61395454, 0.72252121, -0.72252121, 0.61395454],
        [1.03740582, 0.96512163, -0.96512163, 1.03740582],
        [0.81294727, -0.01561215, 0.01561215, 0.81294727],
        [0.09494793, 0.88061383, -0.88061383, 0.09494793],
        [-0.35772628, 1.17679072, -1.17679072, -0.35772628],
        [0.49695525, 0.16147493, -0.16147493, 0.49695525],
        [-0.32299587, 0.44293726, -0.44293726, -0.32299587],
        [-0.72274272, 0.51109849, -0.51109849, -0.72274272],
        [-0.16474317, -0.56787676, 0.56787676, -0.16474317],
        [-0.97859858, -0.45892448, 0.45892448, -0.97859858],
        [-0.42746846, -1.05407622, 1.05407622, -0.42746846],
        [0.51310245, -0.8432099, 0.8432099, 0.51310245],
        [1.2550222, -0.17791612, 0.17791612, 1.2550222],
    ]

    pointlistD3v1 = [
        [0.57863806, -0.93198782, 0.93198782, 0.57863806],
        [1.16819202, 0.20517804, -0.20517804, 1.16819202],
        [-0.68051864, -0.97162374, 0.97162374, -0.68051864],
        [-0.59790946, -0.09166605, 0.09166605, -0.59790946],
        [0.350262, 0.5254438, -0.5254438, 0.350262],
        [0.30295808, -0.51612308, 0.51612308, 0.30295808],
        [0.94265909, -0.40006609, 0.40006609, 0.94265909],
        [-0.11101738, -1.03555541, 1.03555541, -0.11101738],
    ] 
    
    pointlistD3v2 = [
        [-0.95040539, 0.42519812, -0.42519812, -0.95040539],
        [-0.90905749, -0.67886449, 0.67886449, -0.90905749], 
        [0.27366296, -1.11402019, 1.11402019, 0.27366296], 
        [-0.39735878, -0.35625519, 0.35625519, -0.39735878], 
        [0.41298282, -0.37997875, 0.37997875, 0.41298282], 
        [-0.80163061, -0.31612061, 0.31612061, -0.80163061], 
        [0.44362567, -0.80529768, 0.80529768, 0.44362567], 
        [0.21684883, 0.65408395, -0.65408395, 0.21684883],
    ]
    
    pointlistD3v3 = [
        [0.51630871, -1.22405262, 1.22405262, 0.51630871], 
        [-0.82581514, 0.88918515, -0.88918515, -0.82581514], 
        [0.41611041, 1.40065629, -1.40065629, 0.41611041],
        [-0.77553896, -0.38058551, 0.38058551, -0.77553896],
        [-0.53695919, -0.04815008, 0.04815008, -0.53695919],
        [0.0656359, 0.52181275, -0.52181275, 0.0656359],
        [0.63208816, -0.30365848, 0.30365848, 0.63208816],
        [1.20010965, 0.60014593, -0.60014593, 1.20010965],
        ]
    
    pointlistD3v4 = [
        [-0.38983945, -1.14467135, 1.14467135, -0.38983945],
        [-1.16158054, 0.28790215, -0.28790215, -1.16158054],
        [-0.79299043, -0.54624414, 0.54624414, -0.79299043],
        [0.5678252, -0.19872388, 0.19872388, 0.5678252], 
        [0.25991564, -1.12786646, 1.12786646, 0.25991564],
        [-0.81957003, 0.72830491, -0.72830491, -0.81957003], 
        [0.03548759, 0.60160004, -0.60160004, 0.03548759], 
        [-0.5008095, -0.3371377, 0.3371377, -0.5008095],
        ]

    pointlistD2 = [
        [-0.21655953, 0.36502677, -0.36502677, -0.21655953],
        [0.42437394, 0.00505914, -0.00505914, 0.42437394],
        [-0.20783834, -0.36999038, 0.36999038, -0.20783834],
    ]

    listofpointlists = [pointlistD6, pointlistD5, pointlistD4, pointlistD3v4, pointlistD2]

    x0_center = 177.38e6
    x1_center = 176.04e6
    x2_center = 174.675e6
    x3_center = 173.3e6
    x4_center = 171.92e6
    x5_center = 170.52e6
    # x6_center = 169.135e6
    # x7_center = 167.7e6

    # chi = 1.359e6
    bw = 0e6  # will do the same point 5 times
    points = 1

    x0 = np.linspace(x0_center - bw, x0_center + bw, points)
    x1 = np.linspace(x1_center - bw, x1_center + bw, points)
    x2 = np.linspace(x2_center - bw, x2_center + bw, points)
    x3 = np.linspace(x3_center - bw, x3_center + bw, points)
    x4 = np.linspace(x4_center - bw, x4_center + bw, points)
    x5 = np.linspace(x5_center - bw, x5_center + bw, points)

    x54 = np.hstack((x5, x4))
    x543 = np.hstack((x54, x3))
    x5432 = np.hstack((x543, x2))
    x54321 = np.hstack((x5432, x1))
    x543210 = np.hstack((x54321, x0))
    xlist = np.array(x543210, dtype="int").tolist()
    # xlist = np.array(x5, dtype="int").tolist()

    for i in range(3, 4):
        pulselist = listofpulselists[i]
        pointlist = listofpointlists[i]

        for pulse in pulselist:
            for point in range(len(pointlist)):
                parameters = {
                    "modes": ["QUBIT", "CAV", "RR"],
                    "reps": 500,
                    "wait_time": 10e6,
                    "x_sweep": xlist,  # only measuring p5 for D6
                    "qubit_op": "qubit_gaussian_sig250ns_pi_pulse",
                    "cav_op": "coherent_1_long",
                    "cav_amp": 0,
                    # "plot_quad": "I_AVG",
                    "fit_fn": None,
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

                experiment = NSplitSpectroscopy(**parameters)
                experiment.name = (
                    "QML_sparse_PND_D="
                    + str(6-i)
                    + "_"
                    + str(pulse)
                    + "_point{}".format(point + 1)
                )

                experiment.setup_plot(**plot_parameters)
                prof.run(experiment)
