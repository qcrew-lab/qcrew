""" mixer tuning v5 """

from qcrew.control.instruments.meta.mixer_tuner import MixerTuner
from qcrew.control import Stagehand


if __name__ == "__main__":
    with Stagehand() as stage:
        cav, rr, sa, qubit, qubit_ef = stage.CAV, stage.RR, stage.SA, stage.QUBIT, stage.QUBIT_EF
        # get an already configured qm after making changes to modes
        qm = stage.QM

        mxrtnr = MixerTuner(qubit_ef, sa=sa, qm=qm)
        mxrtnr.tune()



