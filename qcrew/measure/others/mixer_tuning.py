""" mixer tuning v5 """

import matplotlib.pyplot as plt

from qcrew.control.instruments.meta.mixer_tuner import MixerTuner
from qcrew.control import Stagehand
from qcrew.measure.resonator_characterization.rr_amp_calibration import RRAmpCalibration

if __name__ == "__main__":

    with Stagehand() as stage:

        # sa, qubit, qubit_ef, rr, cav= stage.SA, stage.QUBIT, stage.QUBIT_EF, stage.RR, stage.CAV
        sa, qubit, rr = (
            stage.SA,
            stage.QUBIT,
            stage.RR,
        )
        qm = stage.QM
        mixer_tuner = MixerTuner(sa, qm)

        # this is the mode whose mixer's LO or SB leakage you are tuning
        mode = qubit

        # minimize LO leakage

        # use brute force (BF) minimizer
        bf_params_lo = {
            # range of DC offsets you want to sweep to tune LO
            "offset_range": (-0.2, 0.2),  # (min = -0.5, max = 0.5)
            # number of DC offset sweep points in the given range i.e. decide step size
            "num_points": 21,
            # number of iterations of the minimization you want to run
            "num_iterations": 5,
            # after each iteration, the sweep range will be reduced by this factor
            "range_divider": 2,
            # if you want the full minimization traceback, set this to True
            "verbose": True,
            # if you want a plot that shows minimization summary, set this to True
            "plot": False,
        }

        mixer_tuner.tune_lo(mode=mode, method="BF", **bf_params_lo)

        # user Nelder-Mead (NM) minimizer
        # mixer_tuner.tune_lo(mode=mode, method="NM")

        # minimize SB leakage

        # use brute force (BF) minimizer
        bf_params_sb = {
            # range of DC offsets you want to sweep to tune LO
            "offset_range": (-0.2, 0.2),  # (min = -0.5, max = 0.5)
            # number of DC offset sweep points in the given range i.e. decide step size
            "num_points": 21,
            # number of iterations of the minimization you want to run
            "num_iterations": 5,
            # after each iteration, the sweep range will be reduced by this factor
            "range_divider": 2,
            # if you want the full minimization traceback, set this to True
            "verbose": True,
            # if you want a plot that shows minimization summary, set this to True
            "plot": False,
        }

        mixer_tuner.tune_sb(mode=mode, method="BF", **bf_params_lo)

        # user Nelder-Mead (NM) minimizer
        # mixer_tuner.tune_sb(mode=mode, method="NM")
