""" freq sweep v5 """

from time import time
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
<<<<<<< HEAD
        rr, sa, qubit = stage.RR, stage.SA, stage.QUBIT
        mode = qubit   # select the mode whose spectrum you want to sweep
=======
        rr, sa, qubit, cav, qubit_ef = stage.RR, stage.SA, stage.QUBIT, stage.CAV, stage.QUBIT_EF
        mode = qubit # select the mode whose spectrum you want to sweep
>>>>>>> 9aa82c38fe04c7565f5f6e9352cb821b7fa7507a
        job = stage.QM.execute(get_qua_program())  # play IF to mode
        sweep_parameters = {  # set sweep parameters
            "center": mode.lo_freq,
            "span": 500e6,
            "rbw": Sa124.default_rbw,
            "ref_power": Sa124.default_ref_power,
        }
        get_sweep()
        
        job.halt()
