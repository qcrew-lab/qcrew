""" freq sweep v5 """

from time import time
import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qcrew.control.instruments import Sa124
from qm import qua


def get_qua_program(mode):
    with qua.program() as play_constant_pulse:
        with qua.infinite_loop_():
            mode.play("constant_pulse", ampx=1)
    return play_constant_pulse


def get_sweep(mode, sa, qm, **sweep_params):
    job = qm.execute(get_qua_program(mode))  # play IF to mode
    freqs, amps = sa.sweep(**sweep_params)  # get, plot, show sweep
    plt.plot(freqs, amps)
    plt.show()
    job.halt()


if __name__ == "__main__":

    with Stagehand() as stage:
        # sa, qubit, qubit_ef, rr, cav = stage.SA, stage.QUBIT, stage.QUBIT_EF, stage.RR, stage.CAV
        sa, qubit, rr = (
            stage.SA,
            stage.QUBIT,
            stage.RR,
        )
        # rr.int_freq = -50e6
        # rr.lo_freq = 7.5e9

        mode = rr  # select the mode whose spectrum you want to sweep

        sweep_parameters = {  # set sweep parameters
            "center": mode.lo_freq, #1e9,  
            "span": 650e6,
            "rbw": Sa124.default_rbw,
            "ref_power": Sa124.default_ref_power,
        }
        get_sweep(mode, sa, stage.QM, **sweep_parameters)
