""" """

import matplotlib.pyplot as plt
from qm import qua
from qcrew.control.modes.mode import Mode
from qcrew.control.stage.stagehand import Stagehand


def get_qua_program(mode: Mode):
    with qua.program() as play_constant_pulse:
        with qua.infinite_loop_():
            mode.play("constant_pulse")
    return play_constant_pulse


if __name__ == " __main__":

    with Stagehand() as stage:
        qubit, rr, sa = stage.QUBIT, stage.RR, stage.SA

        qubit.lo_freq = 5e9
        qubit.int_freq = -50e6

        rr.lo_freq = 8e9
        rr.int_freq = -100e6

        qm = stage.QM
        job = qm.execute(get_qua_program(qubit))

        freqs, amps = sa.sweep(center=qubit.lo_freq, span=250e6)
        plt.plot(freqs, amps)
        plt.show()
