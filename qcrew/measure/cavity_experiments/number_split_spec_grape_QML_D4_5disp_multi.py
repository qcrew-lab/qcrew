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

        qua.update_frequency(qubit.name, 60e6)
        if self.cav_grape == "vacuum":
            pass
        elif self.cav_grape == "coh1":
            cav.play(self.cav_op)
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
        qua.align(cav.name, qubit.name, rr.name)
        qua.wait(int(self.wait_time // 4), cav.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    pulselist = [
        # "grape_fock2_pulse",
        "grape_fock3_pulse",
        "grape_fock02_pulse",
        # "grape_fock03_pulse",
        # "grape_fock12_pulse",
        # "grape_fock13_pulse",
    ]

    pointlist = [
        [8.62484599e-01, -5.36294140e-01, 5.36294140e-01, 8.62484599e-01],
        [-7.03951269e-01, -5.37096130e-01, 5.37096130e-01, -7.03951269e-01],
        [1.35791982e-01, 7.04307470e-01, -7.04307470e-01, 1.35791982e-01],
        [7.20124045e-04, -1.00766166e00, 1.00766166e00, 7.20124045e-04],
        [-7.51109906e-01, -1.14075000e-03, 1.14075000e-03, -7.51109906e-01],
        [7.52191452e-01, 3.52538890e-01, -3.52538890e-01, 7.52191452e-01],
        [-3.89869418e-01, 5.28115870e-01, -5.28115870e-01, -3.89869418e-01],
        [9.49191868e-02, -1.85690400e-01, 1.85690400e-01, 9.49191868e-02],
    ]
    frearray = [
        int(57.82e6),
        int(57.87e6),
        int(57.92e6),
        int(58.53e6),
        int(58.58e6),
        int(58.63e6),
        int(59.24e6),
        int(59.29e6),
        int(59.34e6),
        int(59.9e6),
        int(59.95e6),
        int(60e6),
    ]

    # frearray = [int(57.87e6), int(58.58e6), int(59.29e6), int(59.95e6),]

    for pulse in pulselist:
        for i in range(len(pointlist)):
            parameters = {
                "modes": ["QUBIT", "CAVB", "RR"],
                "reps": 2000,
                "wait_time": 6000e3,
                "x_sweep": frearray,
                "qubit_op": "gaussian_pi_pulse_selective",
                "cav_op": "gaussian_coh1",
                "cav_amp": 0,
                "plot_quad": "I_AVG",
                "fetch_period": 20,
                "qubit_grape": pulse,
                "cav_grape": pulse,
                "point": pointlist[i],
            }

            plot_parameters = {
                "xlabel": "Qubit pulse frequency (Hz)",
            }

            experiment = NSplitSpectroscopy(**parameters)

            experiment.name = (
                "QML_number_split_spec_" + pulse + "_point{}".format(i + 1)
            )

            experiment.setup_plot(**plot_parameters)

            prof.run(experiment)
