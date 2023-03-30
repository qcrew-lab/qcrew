""" mixer tuning v5 """

from qcrew.control.instruments.meta.mixer_tuner import MixerTuner
from qcrew.control import Stagehand


if __name__ == "__main__":
    with Stagehand() as stage:
        rr, sa = stage.RR, stage.SA
        # get an already configured qm after making changes to modes
        qm = stage.QM

        mxrtnr = MixerTuner(rr, sa=sa, qm=qm)
        mxrtnr.tune()
