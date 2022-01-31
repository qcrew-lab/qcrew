"""
Script for spectrum analysis of RF signals.
"""

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qcrew.control.instruments import Sa124
from qm import qua


def get_qua_program():
    with qua.program() as play_constant_pulse:
        with qua.infinite_loop_():
            mode.play("constant_pulse", ampx=2.0)
    return play_constant_pulse


def get_sweep():
    freqs, amps = sa.sweep(**sweep_parameters)  # get, plot, show sweep
    plt.plot(freqs, amps)


if __name__ == "__main__":

    with Stagehand() as stage:
        rr, sa = stage.RR, stage.SA
        mode = rr  # select the mode whose spectrum you want to sweep
        rr.lo_freq = 7.63e9

        job = stage.QM.execute(get_qua_program())  # play IF to mode

        sweep_parameters = {  # set sweep parameters
            "center": mode.lo_freq,
            "span": 300e6,
            "rbw": Sa124.default_rbw,
            "ref_power": Sa124.default_ref_power,
        }
        get_sweep() 
        job.halt()
