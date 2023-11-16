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
            # qua.play("digital_pulse", "QUBIT_EF")
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
        sa, cav, qubit, rr = (
            stage.SA,
            stage.CAVITY,
            stage.QUBIT,
            stage.RR,
        )

        mode = qubit  # select the mode whose spectrum you want to sweep

        sweep_parameters = {  # set sweep parameters
            "center": mode.lo_freq,
            "span": 400e6,
            "rbw": Sa124.default_rbw,
            "ref_power": Sa124.default_ref_power,
        }
        get_sweep(mode, sa, stage.QM, **sweep_parameters)
