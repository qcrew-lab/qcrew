""" freq sweep v5 """

import matplotlib.pyplot as plt
from qcrew.control.instruments.signal_hound.sa124 import Sa124
from qcrew.control.stage.stagehand import Stagehand
from qm import qua


def get_qua_program():
    with qua.program() as play_constant_pulse:
        with qua.infinite_loop_():
            mode.play("constant_pulse")
    return play_constant_pulse


def get_sweep():
    freqs, amps = sa.sweep(**sweep_parameters)  # get, plot, show sweep
    plt.plot(freqs, amps)


if __name__ == "__main__":

    with Stagehand() as stage:
        qubit, rr, sa = stage.QUBIT, stage.RR, stage.SA

        mode = qubit  # select the mode whose spectrum you want to sweep

        job = stage.QM.execute(get_qua_program())  # play IF to mode

        sweep_parameters = {  # set sweep parameters
            "center": mode.lo_freq,
            "span": 250e6,
            "rbw": Sa124.default_rbw,
            "ref_power": Sa124.default_ref_power,
        }
        get_sweep()
        job.halt()
