""" Time of flight experiment """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np


def get_qua_program(mode):
    with qua.program() as play_pulse:
        with qua.infinite_loop_():
            mode.play("constant_cos_pulse")
            qua.wait(200, mode.name)
    return play_pulse


if __name__ == "__main__":

    with Stagehand() as stage:

        rr, qubit = stage.RR, stage.QUBIT

        # Execute script
        qm = stage.QM
        job = stage.QM.execute(get_qua_program(qubit))  # play IF to mode
