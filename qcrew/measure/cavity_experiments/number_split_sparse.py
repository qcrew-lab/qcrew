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
    
    pulselist = [
        "vacuum",
        "grape_fock1_pulse",
        "grape_fock2_pulse",
        "grape_fock3_pulse",
        "grape_fock4_pulse",
        "grape_fock5_pulse",
        "grape_fock6_pulse",
        "grape_fock7_pulse",
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
        [0.0, 0.0, 0.0, 0.0],
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
        [0.0, 0.0, 0.0, 0.0],
    ]

    x0_center = 177.4e6
    x1_center = 176.05e6
    x2_center = 174.69e6
    x3_center = 173.325e6
    x4_center = 171.915e6
    x5_center = 170.535e6
    x6_center = 169.135e6
    x7_center = 167.7e6

    chi = 1.359e6
    bw = 0.3e6
    points = 31

    x0 = np.linspace(x0_center - bw, x0_center + bw, points)
    x1 = np.linspace(x1_center - bw, x1_center + bw, points)
    x2 = np.linspace(x2_center - bw, x2_center + bw, points)
    x3 = np.linspace(x3_center - bw, x3_center + bw, points)
    x4 = np.linspace(x4_center - bw, x4_center + bw, points)

    x43 = np.hstack((x4, x3))
    x432 = np.hstack((x43, x2))
    x4321 = np.hstack((x432, x1))
    x43210 = np.hstack((x4321, x0))
    xlist = np.array(x43210, dtype="int").tolist()
    # xlist = np.array(xn, dtype = 'int').tolist()

    for pulse in pulselist:
        for i in range(len(pointlistD5)):
            parameters = {
                "modes": ["QUBIT", "CAV", "RR"],
                "reps": 150,
                "wait_time": 10e6,
                "x_sweep": xlist,
                "qubit_op": "qubit_gaussian_sel_pi_pulse",
                "cav_op": "coherent_1_long",
                "cav_amp": 0,
                # "plot_quad": "I_AVG",
                "fit_fn": "gaussian",
                "single_shot": True,
                "fetch_period": 2,
                "qubit_grape": pulse,
                "cav_grape": pulse,
                "point": pointlistD5[i],
            }

            plot_parameters = {
                "xlabel": "Qubit pulse frequency (Hz)",
                "plot_err": None,
            }

            experiment = NSplitSpectroscopy(**parameters)
            experiment.name = (
                "QML_number_split_spec_" + pulse + "_point{}".format(i + 1)
            )

            experiment.setup_plot(**plot_parameters)
            prof.run(experiment)
