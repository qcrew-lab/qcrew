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
    name = "PND_sparse"

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
        
        # the 1st selection
        if self.cav_grape == "vacuum":
            pass
        elif self.cav_grape == "coh1":
            cav.play(self.cav_op, ampx=(1, 0, 0, 1), phase=-0.25)
        else:
            qubit.play(self.qubit_grape)
            cav.play(self.cav_grape)

        qua.align()
        
        
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
        

        cav.play(self.cav_op, ampx=self.point, phase=-0.25)
        qua.align()
        qua.update_frequency(qubit.name, self.x)  # update qubit pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse

        qua.align(qubit.name, rr.name)  # align modes
        rr.measure((self.I, self.Q))  # measure transmitted signal
        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I > rr.readout_pulse.threshold)
            )
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset
        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

        qua.align(cav.name, qubit.name, rr.name)


# -------------------------------- Execution -----------------------------------
if __name__ == "__main__":
    pulselistD6 = [
        "vacuum",
        # "coh1",
        "grape_fock1",
        "grape_fock2",
        "grape_fock3",
        "grape_fock4",
        # # 'fock5',
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

    # pulselistD5 = [
    #     "vacuum",
    #     "grape_fock1_pulse",
    #     "grape_fock2_pulse",
    #     "grape_fock3_pulse",
    #     "grape_fock4_pulse",
    #     "grape_fock01_pulse",
    #     "grape_fock0i1_pulse",
    #     "grape_fock02_pulse",
    #     "grape_fock0i2_pulse",
    #     "grape_fock03_pulse",
    #     "grape_fock0i3_pulse",
    #     "grape_fock04_pulse",
    #     "grape_fock0i4_pulse",
    #     "grape_fock12_pulse",
    #     "grape_fock1i2_pulse",
    #     "grape_fock13_pulse",
    #     "grape_fock1i3_pulse",
    #     "grape_fock14_pulse",
    #     "grape_fock1i4_pulse",
    #     "grape_fock23_pulse",
    #     "grape_fock2i3_pulse",
    #     "grape_fock24_pulse",
    #     "grape_fock2i4_pulse",
    #     "grape_fock34_pulse",
    #     "grape_fock3i4_pulse",
    #     "coh1",
    # ]

    # pulselistD4 = [
    #     "vacuum",
    #     "grape_fock1_pulse",
    #     "grape_fock2_pulse",
    #     "grape_fock3_pulse",
    #     "grape_fock01_pulse",
    #     "grape_fock0i1_pulse",
    #     "grape_fock02_pulse",
    #     "grape_fock0i2_pulse",
    #     "grape_fock03_pulse",
    #     "grape_fock0i3_pulse",
    #     "grape_fock12_pulse",
    #     "grape_fock1i2_pulse",
    #     "grape_fock13_pulse",
    #     "grape_fock1i3_pulse",
    #     "grape_fock23_pulse",
    #     "grape_fock2i3_pulse",
    #     "coh1",
    # ]

    # pulselistD3 = [
    #     "vacuum",
    #     "grape_fock1_pulse",
    #     "grape_fock2_pulse",
    #     "grape_fock01_pulse",
    #     "grape_fock0i1_pulse",
    #     "grape_fock02_pulse",
    #     "grape_fock0i2_pulse",
    #     "grape_fock12_pulse",
    #     "grape_fock1i2_pulse",
    #     "coh1",
    # ]

    # pulselistD2 = [
    #     "vacuum",
    #     "grape_fock1_pulse",
    #     "grape_fock01_pulse",
    #     "grape_fock0i1_pulse",
    #     "coh1",
    # ]
    listofpulselists = [pulselistD6]

    pointlistD6 = [
        # [0, 0, 0, 0],
        [-0.48187911, -0.41734485, 0.41734485, -0.48187911],
        [0.23174872, 1.11633499, -1.11633499, 0.23174872],
        [0.0504064, 0.37541931, -0.37541931, 0.0504064],
        [1.25255274, 2.10872826, -2.10872826, 1.25255274],
        [-0.49435492, 0.85599798, -0.85599798, -0.49435492],
        [-0.43038545, 0.41356184, -0.41356184, -0.43038545],
        [0.5271912, -0.90156403, 0.90156403, 0.5271912],
        [1.34540633, -0.04074134, 0.04074134, 1.34540633],
        [-0.36563645, 0.07605901, -0.07605901, -0.36563645],
        [1.3414531, -0.85587375, 0.85587375, 1.3414531],
        [1.1784257, -1.86134276, 1.86134276, 1.1784257],
        [0.3304149, -1.83180835, 1.83180835, 0.3304149],
        [0.56397487, 1.92516705, -1.92516705, 0.56397487],
        [-0.92046236, -0.53307494, 0.53307494, -0.92046236],
        [1.61672018, -1.18572345, 1.18572345, 1.61672018],
        [-1.93318253, 0.13849422, -0.13849422, -1.93318253],
        [0.85784998, 0.45969804, -0.45969804, 0.85784998],
        [-0.04803121, -0.36488883, 0.36488883, -0.04803121],
        [-0.30659985, -1.03377411, 1.03377411, -0.30659985],
        [-1.1081292, -0.72326863, 0.72326863, -1.1081292],
        [1.92364126, 1.10348993, -1.10348993, 1.92364126],
        [1.8786748, 0.19507815, -0.19507815, 1.8786748],
        [1.04505317, -0.25137013, 0.25137013, 1.04505317],
        [-1.03336391, 1.86140358, -1.86140358, -1.03336391],
        [-0.14376649, 1.45048125, -1.45048125, -0.14376649],
        [0.36290604, -0.01712708, 0.01712708, 0.36290604],
        [0.70374509, 1.31715702, -1.31715702, 0.70374509],
        [-1.3956255, 0.94748531, -0.94748531, -1.3956255],
        [-1.076281, 0.4800951, -0.4800951, -1.076281],
        [-1.43333961, 0.01043554, -0.01043554, -1.43333961],
        [-0.35077402, -1.28910182, 1.28910182, -0.35077402],
        [0.66220139, -1.09556791, 1.09556791, 0.66220139],
        [0.28725183, -0.52748209, 0.52748209, 0.28725183],
        [-1.84746916, -1.32407537, 1.32407537, -1.84746916],
        [0.47432052, 0.36741188, -0.36741188, 0.47432052],
    ]

    # pointlistD5 = [
    #     [-1.1848571, 0.8096053, -0.8096053, -1.1848571],
    #     [-1.00933408, -0.345056, 0.345056, -1.00933408],
    #     [-1.52223563, -0.04413064, 0.04413064, -1.52223563],
    #     [0.75142788, -0.23834468, 0.23834468, 0.75142788],
    #     [1.4343226, 0.78057228, -0.78057228, 1.4343226],
    #     [0.62963919, 0.40864702, -0.40864702, 0.62963919],
    #     [-0.27088106, -1.04416493, 1.04416493, -0.27088106],
    #     [0.51992756, 0.30268825, -0.30268825, 0.51992756],
    #     [-0.12314268, 1.327761, -1.327761, -0.12314268],
    #     [1.49149501, -0.11959137, 0.11959137, 1.49149501],
    #     [-0.48826335, 0.48197647, -0.48197647, -0.48826335],
    #     [-0.59888712, -1.37432475, 1.37432475, -0.59888712],
    #     [-1.13485624, 1.14524419, -1.14524419, -1.13485624],
    #     [-0.90709117, -0.35785598, 0.35785598, -0.90709117],
    #     [0.11325643, 0.94850705, -0.94850705, 0.11325643],
    #     [1.03258476, 0.91627408, -0.91627408, 1.03258476],
    #     [-0.32048601, 1.7938981, -1.7938981, -0.32048601],
    #     [-0.31784596, 0.26316093, -0.26316093, -0.31784596],
    #     [-0.35660681, -0.55927563, 0.55927563, -0.35660681],
    #     [0.61724267, 1.65008629, -1.65008629, 0.61724267],
    #     [0.59088513, -1.02627816, 1.02627816, 0.59088513],
    #     [0.28546229, 0.28482724, -0.28482724, 0.28546229],
    #     [0.33134764, -0.73575301, 0.73575301, 0.33134764],
    #     [0.26215286, -0.25804249, 0.25804249, 0.26215286],
    # ]

    # pointlistD4 = [
    #     [0.38225617, -0.99489863, 0.99489863, 0.38225617],
    #     [-1.11579993, -0.00203959, 0.00203959, -1.11579993],
    #     [0.61395454, 0.72252121, -0.72252121, 0.61395454],
    #     [1.03740582, 0.96512163, -0.96512163, 1.03740582],
    #     [0.81294727, -0.01561215, 0.01561215, 0.81294727],
    #     [0.09494793, 0.88061383, -0.88061383, 0.09494793],
    #     [-0.35772628, 1.17679072, -1.17679072, -0.35772628],
    #     [0.49695525, 0.16147493, -0.16147493, 0.49695525],
    #     [-0.32299587, 0.44293726, -0.44293726, -0.32299587],
    #     [-0.72274272, 0.51109849, -0.51109849, -0.72274272],
    #     [-0.16474317, -0.56787676, 0.56787676, -0.16474317],
    #     [-0.97859858, -0.45892448, 0.45892448, -0.97859858],
    #     [-0.42746846, -1.05407622, 1.05407622, -0.42746846],
    #     [0.51310245, -0.8432099, 0.8432099, 0.51310245],
    #     [1.2550222, -0.17791612, 0.17791612, 1.2550222],
    # ]

    # pointlistD3 = [
    #     [0.57863806, -0.93198782, 0.93198782, 0.57863806],
    #     [1.16819202, 0.20517804, -0.20517804, 1.16819202],
    #     [-0.68051864, -0.97162374, 0.97162374, -0.68051864],
    #     [-0.59790946, -0.09166605, 0.09166605, -0.59790946],
    #     [0.350262, 0.5254438, -0.5254438, 0.350262],
    #     [0.30295808, -0.51612308, 0.51612308, 0.30295808],
    #     [0.94265909, -0.40006609, 0.40006609, 0.94265909],
    #     [-0.11101738, -1.03555541, 1.03555541, -0.11101738],
    # ]

    # pointlistD2 = [
    #     [-0.21655953, 0.36502677, -0.36502677, -0.21655953],
    #     [0.42437394, 0.00505914, -0.00505914, 0.42437394],
    #     [-0.20783834, -0.36999038, 0.36999038, -0.20783834],
    # ]

    listofpointlists = [pointlistD6]

    x0_center = -60e6
    x1_center = -61.35e6
    x2_center = -62.72e6
    x3_center = -64.08e6
    x4_center = -65.47e6
    x5_center = -66.86e6
    # x6_center = 169.135e6
    # x7_center = 167.7e6

    chi = 1.359e6
    bw = 0e6  # will do the same point 5 times
    points = 5

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
    xlist = np.array(x5, dtype="int").tolist() # only p5
    # xlist = np.array(x543210, dtype="int").tolist()  

    for dim in range(1):
        pulselist = listofpulselists[0]
        pointlist = listofpointlists[0]

        for pulse in pulselist:
            for point in range(len(pointlist)):
                parameters = {
                    "modes": ["QUBIT", "CAV", "RR"],
                    "reps": 200,
                    "wait_time": 16e6,
                    "x_sweep": xlist,  # only measuring p5 for D6
                    "qubit_op": "qubit_gaussian_sig250ns_pi_pulse",
                    "cav_op": "coherent_1_long",
                    "cav_amp": 0,
                    # "plot_quad": "I_AVG",
                    "fit_fn": None,
                    "single_shot": True,
                    "fetch_period": 4,
                    "qubit_grape": pulse,
                    "cav_grape": pulse,
                    "point": pointlist[point],
                }

                plot_parameters = {
                    "xlabel": "Qubit pulse frequency (Hz)",
                    "plot_err": None,
                    "skip_plot": True,
                }

                experiment = NSplitSpectroscopy(**parameters)
                experiment.name = (
                    "QML_sparse_PND_D="
                    + str(6)
                    + "_"
                    + str(pulse)
                    + "_point{}".format(point + 1)
                )

                experiment.setup_plot(**plot_parameters)
                prof.run(experiment)
