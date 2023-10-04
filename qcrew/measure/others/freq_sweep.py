""" freq sweep v5 """

from time import time
import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qcrew.control.instruments import Sa124
from qm import qua


def get_qua_program(mode):
    with qua.program() as play_constant_pulse:
        with qua.infinite_loop_():
            mode.play("constant_pulse", length=(1400 - 500), ampx=1)
    return play_constant_pulse


def get_sweep(mode, sa, qm, **sweep_params):
    job = qm.execute(get_qua_program(mode))  # play IF to mode
    freqs, amps = sa.sweep(**sweep_params)  # get, plot, show sweep
    plt.plot(freqs, amps)
    plt.show()
    job.halt()


if __name__ == "__main__":

    with Stagehand() as stage:
        # rr, sa = stage.RR, stage.SA
        rr, qubit, rr_drive, qubit_ef, cav, cav_drive, sa = (
            stage.RR,
            stage.QUBIT,
            stage.RR_DRIVE,
            stage.QUBIT_EF,
            stage.CAV,
            stage.CAV_DRIVE,
            stage.SA,
        )
        
        mode = cav # select the mode whose spectrum you want to sweep

        job = stage.QM.execute(get_qua_program(mode))  # play IF to mode
        
        sweep_parameters = {  # set sweep parameters
            "center": mode.lo_freq,
            "span":250e6,
            "rbw": Sa124.default_rbw,
            "ref_power": Sa124.default_ref_power,
        }
        get_sweep(mode, sa, stage.QM, **sweep_parameters)
