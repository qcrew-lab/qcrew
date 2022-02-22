""" mixer tuning v5 """

from qcrew.control.instruments.meta.mixer_tuner import MixerTuner
from qcrew.control import Stagehand


if __name__ == "__main__":
    with Stagehand() as stage:
        rr, sa, lb_rr, qubit, qubit_drive = stage.RR, stage.SA, stage.LB_RR, stage.QUBIT, stage.QUBIT_DRIVE
        # qubit.lo_freq = 4.533287e9
        #qubit.lo_freq = 4.5e9
        # qubit.int_freq = -88e6

        # rr.lo_freq = 7.4969e9
        # rr.int_freq = -50e6 

        # get an already configured qm after making changes to modes
        qm = stage.QM

        mxrtnr = MixerTuner(qubit, sa=sa, qm=qm)
        mxrtnr.tune()
