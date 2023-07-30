"""
A python class describing a qubit spectroscopy using QM.
This class serves as a QUA script generator with user-defined parameters.
"""

from typing import ClassVar

from qcrew.control import Stagehand
from qcrew.control import professor as prof
from qcrew.measure.experiment import Experiment
from qcrew.analyze import fit
from qm import qua
import matplotlib.pyplot as plt
import numpy as np
import h5py


import time
import numpy as np

from qcrew.analyze import stats
from qcrew.analyze.plotter import Plotter
from qcrew.control import Stagehand
from qcrew.control.instruments.qm import QMResultFetcher
from qcrew.helpers import logger
from qcrew.helpers.datasaver import DataSaver, initialise_database
from qcrew.measure.experiment import Experiment

import matplotlib.pyplot as plt
from IPython import display


from qcrew.measure.qubit_experiments_GE.qubit_spec import QubitSpectroscopy

# ---------------------------------- Class -------------------------------------


class Wigner3point(Experiment):

    name = "wigner_3point"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(
        self,
        qubit_op,
        qubit_op_wigner,
        cav_op,
        cav_op_wigner,
        delay,
        fit_fn=None,
        **other_params
    ):
        self.cav_op = cav_op
        self.qubit_op = qubit_op
        self.cav_op_wigner = cav_op_wigner
        self.qubit_op_wigner = qubit_op_wigner
        self.fit_fn = fit_fn
        self.delay = delay

        self.probing_list = [
            # pulse name, X, Y
            ("qctrl_fock_0p3", (-0.64814162, -0.36008861)),
            ("qctrl_fock_0p3", (-0.00490393, 0.26529024)),
            ("qctrl_fock_0p3", (-0.02240402, 0.74343831)),
            ("qctrl_fock_0p3", (-0.53720059, 1.03749518)),
            ("qctrl_fock_0p3", (-0.60380164, -1.0046089)),
            ("qctrl_fock_0p3", (0.59025967, 1.01336611)),
            ("qctrl_fock_0p3", (0.60430717, -1.01099343)),
            ("qctrl_fock_0p3", (0.64472497, -0.37598059)),
            ("qctrl_fock_0p3", (0.23570834, -0.1320831)),
            ("qctrl_fock_0p3", (-0.59650228, 0.35521383)),
            ("qctrl_fock_0p3", (-0.0128941, -0.7098708)),
            ("qctrl_fock_0p3", (0.59471572, 0.3513811)),
            ("qctrl_fock_0p3", (1.17389003, -0.04054449)),
            ("qctrl_fock_0p3", (-1.16925829, -0.01832806)),
            ("qctrl_fock_0p3", (-0.22871322, -0.13728926)),
            ("qctrl_fock_0pi1", (-0.64814162, -0.36008861)),
            ("qctrl_fock_0pi1", (-0.00490393, 0.26529024)),
            ("qctrl_fock_0pi1", (-0.02240402, 0.74343831)),
            ("qctrl_fock_0pi1", (-0.53720059, 1.03749518)),
            ("qctrl_fock_0pi1", (-0.60380164, -1.0046089)),
            ("qctrl_fock_0pi1", (0.59025967, 1.01336611)),
            ("qctrl_fock_0pi1", (0.60430717, -1.01099343)),
            ("qctrl_fock_0pi1", (0.64472497, -0.37598059)),
            ("qctrl_fock_0pi1", (0.23570834, -0.1320831)),
            ("qctrl_fock_0pi1", (-0.59650228, 0.35521383)),
            ("qctrl_fock_0pi1", (-0.0128941, -0.7098708)),
            ("qctrl_fock_0pi1", (0.59471572, 0.3513811)),
            ("qctrl_fock_0pi1", (1.17389003, -0.04054449)),
            ("qctrl_fock_0pi1", (-1.16925829, -0.01832806)),
            ("qctrl_fock_0pi1", (-0.22871322, -0.13728926)),
            # ("qctrl_fock_0pi2", (-0.64814162, -0.36008861)),
            # ("qctrl_fock_0pi2", (-0.00490393, 0.26529024)),
            # ("qctrl_fock_0pi2", (-0.02240402, 0.74343831)),
            # ("qctrl_fock_0pi2", (-0.53720059, 1.03749518)),
            # ("qctrl_fock_0pi2", (-0.60380164, -1.0046089)),
            # ("qctrl_fock_0pi2", (0.59025967, 1.01336611)),
            # ("qctrl_fock_0pi2", (0.60430717, -1.01099343)),
            # ("qctrl_fock_0pi2", (0.64472497, -0.37598059)),
            # ("qctrl_fock_0pi2", (0.23570834, -0.1320831)),
            # ("qctrl_fock_0pi2", (-0.59650228, 0.35521383)),
            # ("qctrl_fock_0pi2", (-0.0128941, -0.7098708)),
            # ("qctrl_fock_0pi2", (0.59471572, 0.3513811)),
            # ("qctrl_fock_0pi2", (1.17389003, -0.04054449)),
            # ("qctrl_fock_0pi2", (-1.16925829, -0.01832806)),
            # ("qctrl_fock_0pi2", (-0.22871322, -0.13728926)),
            # ("qctrl_fock_0pi3", (-0.64814162, -0.36008861)),
            # ("qctrl_fock_0pi3", (-0.00490393, 0.26529024)),
            # ("qctrl_fock_0pi3", (-0.02240402, 0.74343831)),
            # ("qctrl_fock_0pi3", (-0.53720059, 1.03749518)),
            # ("qctrl_fock_0pi3", (-0.60380164, -1.0046089)),
            # ("qctrl_fock_0pi3", (0.59025967, 1.01336611)),
            # ("qctrl_fock_0pi3", (0.60430717, -1.01099343)),
            # ("qctrl_fock_0pi3", (0.64472497, -0.37598059)),
            # ("qctrl_fock_0pi3", (0.23570834, -0.1320831)),
            # ("qctrl_fock_0pi3", (-0.59650228, 0.35521383)),
            # ("qctrl_fock_0pi3", (-0.0128941, -0.7098708)),
            # ("qctrl_fock_0pi3", (0.59471572, 0.3513811)),
            # ("qctrl_fock_0pi3", (1.17389003, -0.04054449)),
            # ("qctrl_fock_0pi3", (-1.16925829, -0.01832806)),
            # ("qctrl_fock_0pi3", (-0.22871322, -0.13728926)),
            # ("qctrl_fock_1p2", (-0.64814162, -0.36008861)),
            # ("qctrl_fock_1p2", (-0.00490393, 0.26529024)),
            # ("qctrl_fock_1p2", (-0.02240402, 0.74343831)),
            # ("qctrl_fock_1p2", (-0.53720059, 1.03749518)),
            # ("qctrl_fock_1p2", (-0.60380164, -1.0046089)),
            # ("qctrl_fock_1p2", (0.59025967, 1.01336611)),
            # ("qctrl_fock_1p2", (0.60430717, -1.01099343)),
            # ("qctrl_fock_1p2", (0.64472497, -0.37598059)),
            # ("qctrl_fock_1p2", (0.23570834, -0.1320831)),
            # ("qctrl_fock_1p2", (-0.59650228, 0.35521383)),
            # ("qctrl_fock_1p2", (-0.0128941, -0.7098708)),
            # ("qctrl_fock_1p2", (0.59471572, 0.3513811)),
            # ("qctrl_fock_1p2", (1.17389003, -0.04054449)),
            # ("qctrl_fock_1p2", (-1.16925829, -0.01832806)),
            # ("qctrl_fock_1p2", (-0.22871322, -0.13728926)),
            # ("qctrl_fock_1p3", (-0.64814162, -0.36008861)),
            # ("qctrl_fock_1p3", (-0.00490393, 0.26529024)),
            # ("qctrl_fock_1p3", (-0.02240402, 0.74343831)),
            # ("qctrl_fock_1p3", (-0.53720059, 1.03749518)),
            # ("qctrl_fock_1p3", (-0.60380164, -1.0046089)),
            # ("qctrl_fock_1p3", (0.59025967, 1.01336611)),
            # ("qctrl_fock_1p3", (0.60430717, -1.01099343)),
            # ("qctrl_fock_1p3", (0.64472497, -0.37598059)),
            # ("qctrl_fock_1p3", (0.23570834, -0.1320831)),
            # ("qctrl_fock_1p3", (-0.59650228, 0.35521383)),
            # ("qctrl_fock_1p3", (-0.0128941, -0.7098708)),
            # ("qctrl_fock_1p3", (0.59471572, 0.3513811)),
            # ("qctrl_fock_1p3", (1.17389003, -0.04054449)),
            # ("qctrl_fock_1p3", (-1.16925829, -0.01832806)),
            # ("qctrl_fock_1p3", (-0.22871322, -0.13728926)),
            # ("qctrl_fock_1pi2", (-0.64814162, -0.36008861)),
            # ("qctrl_fock_1pi2", (-0.00490393, 0.26529024)),
            # ("qctrl_fock_1pi2", (-0.02240402, 0.74343831)),
            # ("qctrl_fock_1pi2", (-0.53720059, 1.03749518)),
            # ("qctrl_fock_1pi2", (-0.60380164, -1.0046089)),
            # ("qctrl_fock_1pi2", (0.59025967, 1.01336611)),
            # ("qctrl_fock_1pi2", (0.60430717, -1.01099343)),
            # ("qctrl_fock_1pi2", (0.64472497, -0.37598059)),
            # ("qctrl_fock_1pi2", (0.23570834, -0.1320831)),
            # ("qctrl_fock_1pi2", (-0.59650228, 0.35521383)),
            # ("qctrl_fock_1pi2", (-0.0128941, -0.7098708)),
            # ("qctrl_fock_1pi2", (0.59471572, 0.3513811)),
            # ("qctrl_fock_1pi2", (1.17389003, -0.04054449)),
            # ("qctrl_fock_1pi2", (-1.16925829, -0.01832806)),
            # ("qctrl_fock_1pi2", (-0.22871322, -0.13728926)),
            # ("qctrl_fock_1pi3", (-0.64814162, -0.36008861)),
            # ("qctrl_fock_1pi3", (-0.00490393, 0.26529024)),
            # ("qctrl_fock_1pi3", (-0.02240402, 0.74343831)),
            # ("qctrl_fock_1pi3", (-0.53720059, 1.03749518)),
            # ("qctrl_fock_1pi3", (-0.60380164, -1.0046089)),
            # ("qctrl_fock_1pi3", (0.59025967, 1.01336611)),
            # ("qctrl_fock_1pi3", (0.60430717, -1.01099343)),
            # ("qctrl_fock_1pi3", (0.64472497, -0.37598059)),
            # ("qctrl_fock_1pi3", (0.23570834, -0.1320831)),
            # ("qctrl_fock_1pi3", (-0.59650228, 0.35521383)),
            # ("qctrl_fock_1pi3", (-0.0128941, -0.7098708)),
            # ("qctrl_fock_1pi3", (0.59471572, 0.3513811)),
            # ("qctrl_fock_1pi3", (1.17389003, -0.04054449)),
            # ("qctrl_fock_1pi3", (-1.16925829, -0.01832806)),
            # ("qctrl_fock_1pi3", (-0.22871322, -0.13728926)),
        ]
        self.internal_sweep = [
            ("qctrl_fock_0p3", "D1"),
            ("qctrl_fock_0p3", "D2"),
            ("qctrl_fock_0p3", "D3"),
            ("qctrl_fock_0p3", "D4"),
            ("qctrl_fock_0p3", "D5"),
            ("qctrl_fock_0p3", "D6"),
            ("qctrl_fock_0p3", "D7"),
            ("qctrl_fock_0p3", "D8"),
            ("qctrl_fock_0p3", "D9"),
            ("qctrl_fock_0p3", "D10"),
            ("qctrl_fock_0p3", "D11"),
            ("qctrl_fock_0p3", "D12"),
            ("qctrl_fock_0p3", "D13"),
            ("qctrl_fock_0p3", "D14"),
            ("qctrl_fock_0p3", "D15"),
            ("qctrl_fock_0pi1", "D1"),
            ("qctrl_fock_0pi1", "D2"),
            ("qctrl_fock_0pi1", "D3"),
            ("qctrl_fock_0pi1", "D4"),
            ("qctrl_fock_0pi1", "D5"),
            ("qctrl_fock_0pi1", "D6"),
            ("qctrl_fock_0pi1", "D7"),
            ("qctrl_fock_0pi1", "D8"),
            ("qctrl_fock_0pi1", "D9"),
            ("qctrl_fock_0pi1", "D10"),
            ("qctrl_fock_0pi1", "D11"),
            ("qctrl_fock_0pi1", "D12"),
            ("qctrl_fock_0pi1", "D13"),
            ("qctrl_fock_0pi1", "D14"),
            ("qctrl_fock_0pi1", "D15"),
            # ("qctrl_fock_0pi2", "D1"),
            # ("qctrl_fock_0pi2", "D2"),
            # ("qctrl_fock_0pi2", "D3"),
            # ("qctrl_fock_0pi2", "D4"),
            # ("qctrl_fock_0pi2", "D5"),
            # ("qctrl_fock_0pi2", "D6"),
            # ("qctrl_fock_0pi2", "D7"),
            # ("qctrl_fock_0pi2", "D8"),
            # ("qctrl_fock_0pi2", "D9"),
            # ("qctrl_fock_0pi2", "D10"),
            # ("qctrl_fock_0pi2", "D11"),
            # ("qctrl_fock_0pi2", "D12"),
            # ("qctrl_fock_0pi2", "D13"),
            # ("qctrl_fock_0pi2", "D14"),
            # ("qctrl_fock_0pi2", "D15"),
            # ("qctrl_fock_0pi3", "D1"),
            # ("qctrl_fock_0pi3", "D2"),
            # ("qctrl_fock_0pi3", "D3"),
            # ("qctrl_fock_0pi3", "D4"),
            # ("qctrl_fock_0pi3", "D5"),
            # ("qctrl_fock_0pi3", "D6"),
            # ("qctrl_fock_0pi3", "D7"),
            # ("qctrl_fock_0pi3", "D8"),
            # ("qctrl_fock_0pi3", "D9"),
            # ("qctrl_fock_0pi3", "D10"),
            # ("qctrl_fock_0pi3", "D11"),
            # ("qctrl_fock_0pi3", "D12"),
            # ("qctrl_fock_0pi3", "D13"),
            # ("qctrl_fock_0pi3", "D14"),
            # ("qctrl_fock_0pi3", "D15"),
            # ("qctrl_fock_1p2", "D1"),
            # ("qctrl_fock_1p2", "D2"),
            # ("qctrl_fock_1p2", "D3"),
            # ("qctrl_fock_1p2", "D4"),
            # ("qctrl_fock_1p2", "D5"),
            # ("qctrl_fock_1p2", "D6"),
            # ("qctrl_fock_1p2", "D7"),
            # ("qctrl_fock_1p2", "D8"),
            # ("qctrl_fock_1p2", "D9"),
            # ("qctrl_fock_1p2", "D10"),
            # ("qctrl_fock_1p2", "D11"),
            # ("qctrl_fock_1p2", "D12"),
            # ("qctrl_fock_1p2", "D13"),
            # ("qctrl_fock_1p2", "D14"),
            # ("qctrl_fock_1p2", "D15"),
            # ("qctrl_fock_1p3", "D1"),
            # ("qctrl_fock_1p3", "D2"),
            # ("qctrl_fock_1p3", "D3"),
            # ("qctrl_fock_1p3", "D4"),
            # ("qctrl_fock_1p3", "D5"),
            # ("qctrl_fock_1p3", "D6"),
            # ("qctrl_fock_1p3", "D7"),
            # ("qctrl_fock_1p3", "D8"),
            # ("qctrl_fock_1p3", "D9"),
            # ("qctrl_fock_1p3", "D10"),
            # ("qctrl_fock_1p3", "D11"),
            # ("qctrl_fock_1p3", "D12"),
            # ("qctrl_fock_1p3", "D13"),
            # ("qctrl_fock_1p3", "D14"),
            # ("qctrl_fock_1p3", "D15"),
            # ("qctrl_fock_1pi2", "D1"),
            # ("qctrl_fock_1pi2", "D2"),
            # ("qctrl_fock_1pi2", "D3"),
            # ("qctrl_fock_1pi2", "D4"),
            # ("qctrl_fock_1pi2", "D5"),
            # ("qctrl_fock_1pi2", "D6"),
            # ("qctrl_fock_1pi2", "D7"),
            # ("qctrl_fock_1pi2", "D8"),
            # ("qctrl_fock_1pi2", "D9"),
            # ("qctrl_fock_1pi2", "D10"),
            # ("qctrl_fock_1pi2", "D11"),
            # ("qctrl_fock_1pi2", "D12"),
            # ("qctrl_fock_1pi2", "D13"),
            # ("qctrl_fock_1pi2", "D14"),
            # ("qctrl_fock_1pi2", "D15"),
            # ("qctrl_fock_1pi3", "D1"),
            # ("qctrl_fock_1pi3", "D2"),
            # ("qctrl_fock_1pi3", "D3"),
            # ("qctrl_fock_1pi3", "D4"),
            # ("qctrl_fock_1pi3", "D5"),
            # ("qctrl_fock_1pi3", "D6"),
            # ("qctrl_fock_1pi3", "D7"),
            # ("qctrl_fock_1pi3", "D8"),
            # ("qctrl_fock_1pi3", "D9"),
            # ("qctrl_fock_1pi3", "D10"),
            # ("qctrl_fock_1pi3", "D11"),
            # ("qctrl_fock_1pi3", "D12"),
            # ("qctrl_fock_1pi3", "D13"),
            # ("qctrl_fock_1pi3", "D14"),
            # ("qctrl_fock_1pi3", "D15"),
        ]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr, cav = self.modes  # get the modes

        for point in self.probing_list:
            pulse = point[0]
            D = point[1]
            qua.reset_frame(cav.name)

            if pulse is not "vacuum":
                qubit.play(pulse)
                cav.play(pulse)
                qua.align(cav.name, qubit.name)

            # Wigner measurements
            cav.play(self.cav_op_wigner, ampx=(-D[1], D[0], -D[0], -D[1]), phase=0.5)
            qua.align(cav.name, qubit.name)
            qubit.play(self.qubit_op_wigner)  # play pi/2 pulse around X
            qua.wait(int(self.delay // 4), cav.name, qubit.name)
            qubit.play(self.qubit_op_wigner)  # play pi/2 pulse around X

            # Measure cavity state
            qua.align(qubit.name, rr.name)  # align measurement
            rr.measure((self.I, self.Q))  # measure transmitted signal

            # wait system reset
            qua.align()
            qua.wait(int(self.wait_time // 4), cav.name)

            if self.single_shot:  # assign state to G or E
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )

            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()


class NumberSplitting3point(Experiment):

    name = "number_splitting_3point"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "cav_op",  # operation for displacing the cavity
        "qubit_op_measure",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op_measure, cav_op, qubit_op, fit_fn=None, **other_params):

        self.qubit_op_measure = qubit_op_measure
        self.qubit_op = qubit_op
        self.cav_op = cav_op
        self.fit_fn = fit_fn
        self.probing_list = [
            # pulse name, X, Y
            ("qctrl_fock_0p3", (0.38225617, -0.99489863)),
            ("qctrl_fock_0p3", (-1.11579993, -0.00203959)),
            ("qctrl_fock_0p3", (0.61395454, 0.72252121)),
            ("qctrl_fock_0p3", (1.03740582, 0.96512163)),
            ("qctrl_fock_0p3", (0.81294727, -0.01561215)),
            ("qctrl_fock_0p3", (0.09494793, 0.88061383)),
            ("qctrl_fock_0p3", (-0.35772628, 1.17679072)),
            ("qctrl_fock_0p3", (0.49695525, 0.16147493)),
            ("qctrl_fock_0p3", (-0.32299587, 0.44293726)),
            ("qctrl_fock_0p3", (-0.72274272, 0.51109849)),
            ("qctrl_fock_0p3", (-0.16474317, -0.56787676)),
            ("qctrl_fock_0p3", (-0.97859858, -0.45892448)),
            ("qctrl_fock_0p3", (-0.42746846, -1.05407622)),
            ("qctrl_fock_0p3", (0.51310245, -0.8432099)),
            ("qctrl_fock_0p3", (1.2550222, -0.17791612)),
            ("qctrl_fock_0pi1", (0.38225617, -0.99489863)),
            ("qctrl_fock_0pi1", (-1.11579993, -0.00203959)),
            ("qctrl_fock_0pi1", (0.61395454, 0.72252121)),
            ("qctrl_fock_0pi1", (1.03740582, 0.96512163)),
            ("qctrl_fock_0pi1", (0.81294727, -0.01561215)),
            ("qctrl_fock_0pi1", (0.09494793, 0.88061383)),
            ("qctrl_fock_0pi1", (-0.35772628, 1.17679072)),
            ("qctrl_fock_0pi1", (0.49695525, 0.16147493)),
            ("qctrl_fock_0pi1", (-0.32299587, 0.44293726)),
            ("qctrl_fock_0pi1", (-0.72274272, 0.51109849)),
            ("qctrl_fock_0pi1", (-0.16474317, -0.56787676)),
            ("qctrl_fock_0pi1", (-0.97859858, -0.45892448)),
            ("qctrl_fock_0pi1", (-0.42746846, -1.05407622)),
            ("qctrl_fock_0pi1", (0.51310245, -0.8432099)),
            ("qctrl_fock_0pi1", (1.2550222, -0.17791612)),
            # ("qctrl_fock_0pi2", (0.38225617, -0.99489863)),
            # ("qctrl_fock_0pi2", (-1.11579993, -0.00203959)),
            # ("qctrl_fock_0pi2", (0.61395454, 0.72252121)),
            # ("qctrl_fock_0pi2", (1.03740582, 0.96512163)),
            # ("qctrl_fock_0pi2", (0.81294727, -0.01561215)),
            # ("qctrl_fock_0pi2", (0.09494793, 0.88061383)),
            # ("qctrl_fock_0pi2", (-0.35772628, 1.17679072)),
            # ("qctrl_fock_0pi2", (0.49695525, 0.16147493)),
            # ("qctrl_fock_0pi2", (-0.32299587, 0.44293726)),
            # ("qctrl_fock_0pi2", (-0.72274272, 0.51109849)),
            # ("qctrl_fock_0pi2", (-0.16474317, -0.56787676)),
            # ("qctrl_fock_0pi2", (-0.97859858, -0.45892448)),
            # ("qctrl_fock_0pi2", (-0.42746846, -1.05407622)),
            # ("qctrl_fock_0pi2", (0.51310245, -0.8432099)),
            # ("qctrl_fock_0pi2", (1.2550222, -0.17791612)),
            # ("qctrl_fock_0pi3", (0.38225617, -0.99489863)),
            # ("qctrl_fock_0pi3", (-1.11579993, -0.00203959)),
            # ("qctrl_fock_0pi3", (0.61395454, 0.72252121)),
            # ("qctrl_fock_0pi3", (1.03740582, 0.96512163)),
            # ("qctrl_fock_0pi3", (0.81294727, -0.01561215)),
            # ("qctrl_fock_0pi3", (0.09494793, 0.88061383)),
            # ("qctrl_fock_0pi3", (-0.35772628, 1.17679072)),
            # ("qctrl_fock_0pi3", (0.49695525, 0.16147493)),
            # ("qctrl_fock_0pi3", (-0.32299587, 0.44293726)),
            # ("qctrl_fock_0pi3", (-0.72274272, 0.51109849)),
            # ("qctrl_fock_0pi3", (-0.16474317, -0.56787676)),
            # ("qctrl_fock_0pi3", (-0.97859858, -0.45892448)),
            # ("qctrl_fock_0pi3", (-0.42746846, -1.05407622)),
            # ("qctrl_fock_0pi3", (0.51310245, -0.8432099)),
            # ("qctrl_fock_0pi3", (1.2550222, -0.17791612)),
            # ("qctrl_fock_1p2", (0.38225617, -0.99489863)),
            # ("qctrl_fock_1p2", (-1.11579993, -0.00203959)),
            # ("qctrl_fock_1p2", (0.61395454, 0.72252121)),
            # ("qctrl_fock_1p2", (1.03740582, 0.96512163)),
            # ("qctrl_fock_1p2", (0.81294727, -0.01561215)),
            # ("qctrl_fock_1p2", (0.09494793, 0.88061383)),
            # ("qctrl_fock_1p2", (-0.35772628, 1.17679072)),
            # ("qctrl_fock_1p2", (0.49695525, 0.16147493)),
            # ("qctrl_fock_1p2", (-0.32299587, 0.44293726)),
            # ("qctrl_fock_1p2", (-0.72274272, 0.51109849)),
            # ("qctrl_fock_1p2", (-0.16474317, -0.56787676)),
            # ("qctrl_fock_1p2", (-0.97859858, -0.45892448)),
            # ("qctrl_fock_1p2", (-0.42746846, -1.05407622)),
            # ("qctrl_fock_1p2", (0.51310245, -0.8432099)),
            # ("qctrl_fock_1p2", (1.2550222, -0.17791612)),
            # ("qctrl_fock_1p3", (0.38225617, -0.99489863)),
            # ("qctrl_fock_1p3", (-1.11579993, -0.00203959)),
            # ("qctrl_fock_1p3", (0.61395454, 0.72252121)),
            # ("qctrl_fock_1p3", (1.03740582, 0.96512163)),
            # ("qctrl_fock_1p3", (0.81294727, -0.01561215)),
            # ("qctrl_fock_1p3", (0.09494793, 0.88061383)),
            # ("qctrl_fock_1p3", (-0.35772628, 1.17679072)),
            # ("qctrl_fock_1p3", (0.49695525, 0.16147493)),
            # ("qctrl_fock_1p3", (-0.32299587, 0.44293726)),
            # ("qctrl_fock_1p3", (-0.72274272, 0.51109849)),
            # ("qctrl_fock_1p3", (-0.16474317, -0.56787676)),
            # ("qctrl_fock_1p3", (-0.97859858, -0.45892448)),
            # ("qctrl_fock_1p3", (-0.42746846, -1.05407622)),
            # ("qctrl_fock_1p3", (0.51310245, -0.8432099)),
            # ("qctrl_fock_1p3", (1.2550222, -0.17791612)),
            # ("qctrl_fock_1p3", (0.38225617, -0.99489863)),
            # ("qctrl_fock_1p3", (-1.11579993, -0.00203959)),
            # ("qctrl_fock_1p3", (0.61395454, 0.72252121)),
            # ("qctrl_fock_1p3", (1.03740582, 0.96512163)),
            # ("qctrl_fock_1p3", (0.81294727, -0.01561215)),
            # ("qctrl_fock_1p3", (0.09494793, 0.88061383)),
            # ("qctrl_fock_1p3", (-0.35772628, 1.17679072)),
            # ("qctrl_fock_1p3", (0.49695525, 0.16147493)),
            # ("qctrl_fock_1p3", (-0.32299587, 0.44293726)),
            # ("qctrl_fock_1p3", (-0.72274272, 0.51109849)),
            # ("qctrl_fock_1p3", (-0.16474317, -0.56787676)),
            # ("qctrl_fock_1p3", (-0.97859858, -0.45892448)),
            # ("qctrl_fock_1p3", (-0.42746846, -1.05407622)),
            # ("qctrl_fock_1p3", (0.51310245, -0.8432099)),
            # ("qctrl_fock_1p3", (1.2550222, -0.17791612)),
            # ("qctrl_fock_1pi3", (0.38225617, -0.99489863)),
            # ("qctrl_fock_1pi3", (-1.11579993, -0.00203959)),
            # ("qctrl_fock_1pi3", (0.61395454, 0.72252121)),
            # ("qctrl_fock_1pi3", (1.03740582, 0.96512163)),
            # ("qctrl_fock_1pi3", (0.81294727, -0.01561215)),
            # ("qctrl_fock_1pi3", (0.09494793, 0.88061383)),
            # ("qctrl_fock_1pi3", (-0.35772628, 1.17679072)),
            # ("qctrl_fock_1pi3", (0.49695525, 0.16147493)),
            # ("qctrl_fock_1pi3", (-0.32299587, 0.44293726)),
            # ("qctrl_fock_1pi3", (-0.72274272, 0.51109849)),
            # ("qctrl_fock_1pi3", (-0.16474317, -0.56787676)),
            # ("qctrl_fock_1pi3", (-0.97859858, -0.45892448)),
            # ("qctrl_fock_1pi3", (-0.42746846, -1.05407622)),
            # ("qctrl_fock_1pi3", (0.51310245, -0.8432099)),
            # ("qctrl_fock_1pi3", (1.2550222, -0.17791612)),
        ]
        self.internal_sweep = [
            ("qctrl_fock_0p3", "D1"),
            ("qctrl_fock_0p3", "D2"),
            ("qctrl_fock_0p3", "D3"),
            ("qctrl_fock_0p3", "D4"),
            ("qctrl_fock_0p3", "D5"),
            ("qctrl_fock_0p3", "D6"),
            ("qctrl_fock_0p3", "D7"),
            ("qctrl_fock_0p3", "D8"),
            ("qctrl_fock_0p3", "D9"),
            ("qctrl_fock_0p3", "D10"),
            ("qctrl_fock_0p3", "D11"),
            ("qctrl_fock_0p3", "D12"),
            ("qctrl_fock_0p3", "D13"),
            ("qctrl_fock_0p3", "D14"),
            ("qctrl_fock_0p3", "D15"),
            ("qctrl_fock_0pi1", "D1"),
            ("qctrl_fock_0pi1", "D2"),
            ("qctrl_fock_0pi1", "D3"),
            ("qctrl_fock_0pi1", "D4"),
            ("qctrl_fock_0pi1", "D5"),
            ("qctrl_fock_0pi1", "D6"),
            ("qctrl_fock_0pi1", "D7"),
            ("qctrl_fock_0pi1", "D8"),
            ("qctrl_fock_0pi1", "D9"),
            ("qctrl_fock_0pi1", "D10"),
            ("qctrl_fock_0pi1", "D11"),
            ("qctrl_fock_0pi1", "D12"),
            ("qctrl_fock_0pi1", "D13"),
            ("qctrl_fock_0pi1", "D14"),
            ("qctrl_fock_0pi1", "D15"),
            # ("qctrl_fock_0pi2", "D1"),
            # ("qctrl_fock_0pi2", "D2"),
            # ("qctrl_fock_0pi2", "D3"),
            # ("qctrl_fock_0pi2", "D4"),
            # ("qctrl_fock_0pi2", "D5"),
            # ("qctrl_fock_0pi2", "D6"),
            # ("qctrl_fock_0pi2", "D7"),
            # ("qctrl_fock_0pi2", "D8"),
            # ("qctrl_fock_0pi2", "D9"),
            # ("qctrl_fock_0pi2", "D10"),
            # ("qctrl_fock_0pi2", "D11"),
            # ("qctrl_fock_0pi2", "D12"),
            # ("qctrl_fock_0pi2", "D13"),
            # ("qctrl_fock_0pi2", "D14"),
            # ("qctrl_fock_0pi2", "D15"),
            # ("qctrl_fock_0pi3", "D1"),
            # ("qctrl_fock_0pi3", "D2"),
            # ("qctrl_fock_0pi3", "D3"),
            # ("qctrl_fock_0pi3", "D4"),
            # ("qctrl_fock_0pi3", "D5"),
            # ("qctrl_fock_0pi3", "D6"),
            # ("qctrl_fock_0pi3", "D7"),
            # ("qctrl_fock_0pi3", "D8"),
            # ("qctrl_fock_0pi3", "D9"),
            # ("qctrl_fock_0pi3", "D10"),
            # ("qctrl_fock_0pi3", "D11"),
            # ("qctrl_fock_0pi3", "D12"),
            # ("qctrl_fock_0pi3", "D13"),
            # ("qctrl_fock_0pi3", "D14"),
            # ("qctrl_fock_0pi3", "D15"),
            # ("qctrl_fock_1p2", "D1"),
            # ("qctrl_fock_1p2", "D2"),
            # ("qctrl_fock_1p2", "D3"),
            # ("qctrl_fock_1p2", "D4"),
            # ("qctrl_fock_1p2", "D5"),
            # ("qctrl_fock_1p2", "D6"),
            # ("qctrl_fock_1p2", "D7"),
            # ("qctrl_fock_1p2", "D8"),
            # ("qctrl_fock_1p2", "D9"),
            # ("qctrl_fock_1p2", "D10"),
            # ("qctrl_fock_1p2", "D11"),
            # ("qctrl_fock_1p2", "D12"),
            # ("qctrl_fock_1p2", "D13"),
            # ("qctrl_fock_1p2", "D14"),
            # ("qctrl_fock_1p2", "D15"),
            # ("qctrl_fock_1p3", "D1"),
            # ("qctrl_fock_1p3", "D2"),
            # ("qctrl_fock_1p3", "D3"),
            # ("qctrl_fock_1p3", "D4"),
            # ("qctrl_fock_1p3", "D5"),
            # ("qctrl_fock_1p3", "D6"),
            # ("qctrl_fock_1p3", "D7"),
            # ("qctrl_fock_1p3", "D8"),
            # ("qctrl_fock_1p3", "D9"),
            # ("qctrl_fock_1p3", "D10"),
            # ("qctrl_fock_1p3", "D11"),
            # ("qctrl_fock_1p3", "D12"),
            # ("qctrl_fock_1p3", "D13"),
            # ("qctrl_fock_1p3", "D14"),
            # ("qctrl_fock_1p3", "D15"),
            # ("qctrl_fock_1pi2", "D1"),
            # ("qctrl_fock_1pi2", "D2"),
            # ("qctrl_fock_1pi2", "D3"),
            # ("qctrl_fock_1pi2", "D4"),
            # ("qctrl_fock_1pi2", "D5"),
            # ("qctrl_fock_1pi2", "D6"),
            # ("qctrl_fock_1pi2", "D7"),
            # ("qctrl_fock_1pi2", "D8"),
            # ("qctrl_fock_1pi2", "D9"),
            # ("qctrl_fock_1pi2", "D10"),
            # ("qctrl_fock_1pi2", "D11"),
            # ("qctrl_fock_1pi2", "D12"),
            # ("qctrl_fock_1pi2", "D13"),
            # ("qctrl_fock_1pi2", "D14"),
            # ("qctrl_fock_1pi2", "D15"),
            # ("qctrl_fock_1pi3", "D1"),
            # ("qctrl_fock_1pi3", "D2"),
            # ("qctrl_fock_1pi3", "D3"),
            # ("qctrl_fock_1pi3", "D4"),
            # ("qctrl_fock_1pi3", "D5"),
            # ("qctrl_fock_1pi3", "D6"),
            # ("qctrl_fock_1pi3", "D7"),
            # ("qctrl_fock_1pi3", "D8"),
            # ("qctrl_fock_1pi3", "D9"),
            # ("qctrl_fock_1pi3", "D10"),
            # ("qctrl_fock_1pi3", "D11"),
            # ("qctrl_fock_1pi3", "D12"),
            # ("qctrl_fock_1pi3", "D13"),
            # ("qctrl_fock_1pi3", "D14"),
            # ("qctrl_fock_1pi3", "D15"),
        ]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, cav, rr = self.modes  # get the modes

        # Prepare state
        for point in self.probing_list:
            pulse = point[0]
            D = point[1]
            qua.reset_frame(cav.name)

            qua.update_frequency(qubit.name, qubit.int_freq)
            if pulse is not "vacuum":
                qubit.play(pulse)
                cav.play(pulse)
                qua.align(cav.name, qubit.name)
            # Displace
            cav.play("const_cohstate_1", ampx=(D[1], -D[0], D[0], D[1]), phase=0.5)

            # number splitting
            qua.update_frequency(qubit.name, self.x)
            qua.align(cav.name, qubit.name)  # aself.xlign modes
            qubit.play(self.qubit_op_measure)  # play qubit pulse
            qua.align(qubit.name, rr.name)  # align modes
            rr.measure((self.I, self.Q))  # measure transmitted signal
            qua.align()
            qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

            if self.single_shot:  # assign state to G or E
                qua.assign(
                    self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
                )

            self.QUA_stream_results()  # stream variables (I, Q, x, etc)
            qua.align()


class QubitSpectroscopy(Experiment):

    name = "qubit_spec"

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # fit function
    }

    def __init__(self, qubit_op, fit_fn=None, **other_params):

        self.qubit_op = qubit_op
        self.fit_fn = fit_fn
        # self.internal_sweep = ["28", "140", "280", "420"]

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qua.update_frequency(qubit.name, self.x)  # update resonator pulse frequency
        qubit.play(self.qubit_op)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        if self.single_shot:  # assign state to G or E
            qua.assign(
                self.state, qua.Cast.to_fixed(self.I < rr.readout_pulse.threshold)
            )

        self.QUA_stream_results()  # stream variables (I, 4Q, x, etc)
        qua.align()


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":
    parameters_wigner = {
        "modes": ["QUBIT", "RR", "CAVITY"],
        "reps": 250,  # 250
        "wait_time": 0.7e6,
        "qubit_op": "qctrl_fock_0p1",
        "cav_op": "qctrl_fock_0p1",
        "qubit_op_wigner": "gaussian_pi2",
        "cav_op_wigner": "const_cohstate_1",
        "single_shot": True,
        "fit_fn": "gaussian",
        "delay": 472,
        "fetch_period": 10,
    }

    parameters_nsplit = {
        "modes": ["QUBIT", "CAVITY", "RR"],
        "reps": 250,  # 250
        "wait_time": 0.7e6,
        "x_sweep": (int(-141e6), int(-132.5e6 + 0.05e6 / 2), int(0.05e6)),
        "qubit_op_measure": "gaussian_pi_560",
        "qubit_op": "qctrl_fock_1",
        "cav_op": "qctrl_fock_1",
        "single_shot": True,
        "fit_fn": "gaussian",
        "fetch_period": 10,
    }

    parameters_qubit_spec = {
        "modes": ["QUBIT", "RR"],
        "reps": 1000,
        "wait_time": 60e3,
        "x_sweep": (int(-150e6), int(-120e6 + 0.20e6 / 2), int(0.20e6)),
        "qubit_op": "gaussian_pi",
        "single_shot": True,
        "fit_fn": "gaussian",
    }

    plot_parameters = {
        "skip_plot": True,
    }

    # yoko = stage.YOKO
    # print("Qubit frequency is: ")
    # for i in range(2):
    #     experiment_check_qubit_freq = QubitSpectroscopy(**parameters_qubit_spec)
    #     experiment_check_qubit_freq.setup_plot(**plot_parameters)
    #     prof.run(experiment_check_qubit_freq)

    #     with h5py.File(experiment_check_qubit_freq.filename) as f:
    #         data = f["data"]
    #         state = np.array(data["state"])
    #         freqs = np.array(data["x"])
    #         params = fit.do_fit("gaussian", freqs, state)
    #         qubit_freq = params["x0"].value

    #     print("Qubit frequency is: ", qubit_freq)

    #     ### Calculate current to get target qubit frequency
    #     freq_target = -134.5e6
    #     current_initial = yoko.level
    #     current_target = current_initial + (freq_target - qubit_freq) / 89.5e9
    #     if -1.7e-3 > current_target > 2.1e-3:
    #         yoko.ramp(current_target, yoko.level, np.abs(-0.001e-3))

    # experiment_wigner = Wigner3point(**parameters_wigner)
    # experiment_wigner.setup_plot(**plot_parameters)
    # prof.run(experiment_wigner)

    # experiment_nsplit = NumberSplitting3point(**parameters_nsplit)
    # experiment_nsplit.setup_plot(**plot_parameters)
    # prof.run(experiment_nsplit)

    with Stagehand() as stage:
        qm = stage.QM
        yoko = stage.YOKO

        for i in range(4):
            # Check qubit frequency
            parameters_qubit_spec["modes"] = [stage.QUBIT, stage.RR]
            experiment_check_qubit_freq = QubitSpectroscopy(**parameters_qubit_spec)
            experiment_check_qubit_freq.setup_plot(**plot_parameters)
            qua_program = experiment_check_qubit_freq.QUA_sequence()
            qm_job = qm.execute(qua_program)

            fetcher = QMResultFetcher(handle=qm_job.result_handles)
            stderr = (
                None,
                None,
                None,
            )  # to hold running (stderr, mean, variance * (n-1))

            db = initialise_database(
                exp_name=experiment_check_qubit_freq.name,
                sample_name=stage.sample_name,
                project_name=stage.project_name,
                path=stage.datapath,
            )

            experiment_check_qubit_freq.filename = db.filename
            plotter = Plotter(experiment_check_qubit_freq.plot_setup)
            with DataSaver(db) as datasaver:
                datasaver.add_metadata(experiment_check_qubit_freq.parameters)
                for mode in stage.modes:
                    datasaver.add_metadata(mode.parameters)
                while fetcher.is_fetching:
                    partial_results = fetcher.fetch()
                    num_results = fetcher.count
                    if not partial_results:  # empty dict means no new results available
                        continue
                    datasaver.update_multiple_results(
                        partial_results,
                        save=experiment_check_qubit_freq.live_saving_tags,
                        group="data",
                    )
                    stderr = ([],)
                    qubit_spec_data = experiment_check_qubit_freq.plot_results(
                        plotter, partial_results, num_results, stderr
                    )
                    time.sleep(experiment_check_qubit_freq.fetch_period)

                ##################         SAVE REMAINING DATA         #####################

                datasaver.add_multiple_results(
                    qubit_spec_data, save=qubit_spec_data.keys(), group="data"
                )
                state = np.array(qubit_spec_data["state"])
                freqs = np.array(qubit_spec_data["x"])
                params = fit.do_fit("gaussian", freqs, state)
                qubit_freq = float(params["x0"].value)

                print("Qubit frequency is: ", qubit_freq)

                ### Calculate current to get target qubit frequency
                freq_target = -134.5e6
                current_initial = yoko.level
                current_target = current_initial + (freq_target - qubit_freq) / 89.5e9
                print(current_target)
                if -1.7e-3 > current_target > -2.1e-3:
                    yoko.ramp(current_target, yoko.level, np.abs(-0.001e-3))

            ### Wigner 3 points
            # Check qubit frequency
            parameters_wigner["modes"] = [stage.QUBIT, stage.RR, stage.CAVITY]
            experiment_wigner = Wigner3point(**parameters_wigner)
            experiment_wigner.setup_plot(**plot_parameters)
            qua_program = experiment_wigner.QUA_sequence()
            qm_job = qm.execute(qua_program)

            fetcher = QMResultFetcher(handle=qm_job.result_handles)
            stderr = (
                None,
                None,
                None,
            )  # to hold running (stderr, mean, variance * (n-1))

            db = initialise_database(
                exp_name=experiment_wigner.name,
                sample_name=stage.sample_name,
                project_name=stage.project_name,
                path=stage.datapath,
            )

            experiment_wigner.filename = db.filename
            plotter = Plotter(experiment_wigner.plot_setup)
            with DataSaver(db) as datasaver:
                datasaver.add_metadata(experiment_wigner.parameters)
                for mode in stage.modes:
                    datasaver.add_metadata(mode.parameters)
                while fetcher.is_fetching:
                    partial_results = fetcher.fetch()
                    num_results = fetcher.count
                    if not partial_results:  # empty dict means no new results available
                        continue
                    datasaver.update_multiple_results(
                        partial_results,
                        save=experiment_wigner.live_saving_tags,
                        group="data",
                    )
                    stderr = ([],)
                    wigner_data = experiment_wigner.plot_results(
                        plotter, partial_results, num_results, stderr
                    )
                    time.sleep(experiment_wigner.fetch_period)

                ##################         SAVE REMAINING DATA         #####################

                datasaver.add_multiple_results(
                    wigner_data, save=wigner_data.keys(), group="data"
                )

            ### QRP
            # Check qubit frequency
            parameters_nsplit["modes"] = [stage.QUBIT, stage.CAVITY, stage.RR]
            experiment_nsplit = NumberSplitting3point(**parameters_nsplit)
            experiment_nsplit.setup_plot(**plot_parameters)
            qua_program = experiment_nsplit.QUA_sequence()
            qm_job = qm.execute(qua_program)

            fetcher = QMResultFetcher(handle=qm_job.result_handles)
            stderr = (
                None,
                None,
                None,
            )  # to hold running (stderr, mean, variance * (n-1))

            db = initialise_database(
                exp_name=experiment_nsplit.name,
                sample_name=stage.sample_name,
                project_name=stage.project_name,
                path=stage.datapath,
            )

            experiment_nsplit.filename = db.filename
            plotter = Plotter(experiment_nsplit.plot_setup)
            with DataSaver(db) as datasaver:
                datasaver.add_metadata(experiment_nsplit.parameters)
                for mode in stage.modes:
                    datasaver.add_metadata(mode.parameters)
                while fetcher.is_fetching:
                    partial_results = fetcher.fetch()
                    num_results = fetcher.count
                    if not partial_results:  # empty dict means no new results available
                        continue
                    datasaver.update_multiple_results(
                        partial_results,
                        save=experiment_nsplit.live_saving_tags,
                        group="data",
                    )
                    stderr = ([],)
                    nsplit_data = experiment_nsplit.plot_results(
                        plotter, partial_results, num_results, stderr
                    )
                    time.sleep(experiment_nsplit.fetch_period)

                ##################         SAVE REMAINING DATA         #####################

                datasaver.add_multiple_results(
                    nsplit_data, save=nsplit_data.keys(), group="data"
                )
