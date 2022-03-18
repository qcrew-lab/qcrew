""" freq sweep v5 """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qcrew.control.instruments import Sa124
from qm import qua


def get_qua_program():
    with qua.program() as play_constant_pulse:
        with qua.infinite_loop_():
            mode.play("constant_pulse", ampx=1.0)
    return play_constant_pulse


def get_sweep():
    freqs, amps = sa.sweep(**sweep_parameters)  # get, plot, show sweep
    plt.plot(freqs, amps)


if __name__ == "__main__":

    with Stagehand() as stage:
        sa, qubit = stage.SA, stage.QUBIT
        mode = qubit  # select the mode whose spectrum you want to sweep
        job = stage.QM.execute(get_qua_program())  # play IF to mode

        qubit.lo_freq = 6e9
        qubit.int_freq = -50e6
    
        sweep_parameters = {  # set sweep parameters
            "center": mode.lo_freq,
            "span": 500e6,
            "rbw": Sa124.default_rbw,
            "ref_power": Sa124.default_ref_power,
        }
        get_sweep()
        job.halt()
