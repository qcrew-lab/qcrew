"""
    Just a frequency sweep for Noise rise characterisations for amplifiers
"""

from time import time
import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qcrew.control.instruments import Sa124
from qm import qua
import numpy as np


def get_sweep(path, sa, **sweep_params):
    freqs, amps = sa.sweep(**sweep_params)  # get, plot, show sweep

    plt.figure(figsize=(10, 6), dpi=100)

    plt.suptitle("Frequency Sweep (For Noise Rise Measurement)", fontsize=18)
    plt.title(path)
    plt.plot(freqs, amps)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Amplitude (dBm)")
    plt.grid()
    plt.show()

    return freqs, amps


###############
# Change this #
###############

savepath = r"D:\data\YABBAv4\20230530\pump_off_noise_rise_DJINT_1000MHz.npz"

if 1:
    """
    Plot the results
    """
    pump_on_path = r"D:\data\YABBAv4\20230530\pump_on_noise_rise_DJINT_60MHz.npz"
    pump_off_path = r"D:\data\YABBAv4\20230530\pump_off_noise_rise_DJINT_60MHz.npz"

    pump_on = np.load(pump_on_path, "r")
    pump_off = np.load(pump_off_path, "r")

    plt.figure(figsize=(10, 6), dpi=100)

    plt.suptitle("Frequency Sweep (For Noise Rise Measurement)", fontsize=18)
    plt.title(pump_on_path + "\n" + pump_off_path)

    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Amplitude (dBm)")
    plt.grid()

    plt.plot(pump_on["freq"][1:], pump_on["amp"][1:])
    plt.plot(pump_off["freq"][1:], pump_off["amp"][1:])
    plt.show()


if __name__ == "__main__" and 0:
    with Stagehand() as stage:
        rr, sa = (
            stage.RR,
            stage.SA,
        )

        mode = rr

        sweep_parameters = {  # set sweep parameters
            "center": mode.lo_freq + mode.int_freq,
            "span": 1e9,
            "rbw": Sa124.default_rbw,
            "ref_power": Sa124.default_ref_power,
        }

        freqs, amps = get_sweep(savepath, sa, **sweep_parameters)
        np.savez(savepath, freq=freqs, amp=amps)
