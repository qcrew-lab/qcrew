""" """

import pprint
import matplotlib.pyplot as plt
from qcrew.control.stage.stagehand import Stagehand

with Stagehand() as stage:
    qubit, rr, sa = stage.QUBIT, stage.RR, stage.SA
    #f, a = sa.sweep(center=5e9, span=20e6)
    #plt.plot(f, a)
    #plt.show()

    qm = stage.QM
    qm.close()
