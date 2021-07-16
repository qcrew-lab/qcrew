""" mixer tuning v5 """

from qcrew.control.instruments.meta.mixer_tuner import MixerTuner
from qcrew.control import Stagehand


if __name__ == "__main__":
    with Stagehand() as stage:
        qubit, rr, sa = stage.QUBIT, stage.RR, stage.SA

        # set new carrier and intermediate frequencies to the modes
        qubit.lo_freq = 6e9
        qubit.int_freq = -100e6
        rr.lo_freq = 7e9
        rr.int_freq = -10e6

        # get an already configured qm after making changes to modes
        qm = stage.QM

        mxrtnr = MixerTuner(qubit, rr, sa=sa, qm=qm)
        mxrtnr.tune()
