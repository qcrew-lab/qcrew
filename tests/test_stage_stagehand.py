""" Test stage and stagehand with actual instruments """

import pprint
import matplotlib.pyplot as plt
from qcrew.control.stage import Stagehand

stghand = Stagehand()
stg = stghand.link("QUBIT", "RR", "SA")
qubit, rr, sa = stg["QUBIT"], stg["RR"], stg["SA"]
