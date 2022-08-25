""" Script that generates OCT pulse after you give it rotations """

import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import qutip as qt

from qcrew.measure.ECD_control.ECD_control.ECD_pulse_construction.ECD_pulse_construction import (
    FakeQubit,
    FakeStorage,
    conditional_displacement_circuit,
    pulse_slice,
)
from qcrew.measure.ECD_control.ECD_control.ECD_optimization.batch_optimizer import (
    BatchOptimizer,
)

# OCT_ROTATIONS_PATH = Path(__file__).resolve().parents[4] / "config/oct_rotations"
OCT_PULSES_PATH = Path(__file__).resolve().parents[4] / "config/oct_pulses"

if __name__ == "__main__":

    cavity__load_path = "20222508_150611_oct_pulse_cavity_.npz"
    qubit__load_path = "20222508_150611_oct_pulse_qubit_.npz"
    cav_len = len(cavity__load_path)
    qubit_len = len(qubit__load_path)
    cavity_dac_pulse = np.load(OCT_PULSES_PATH / cavity__load_path)["oct_pulse"]
    qubit_dac_pulse = np.load(OCT_PULSES_PATH / qubit__load_path)["oct_pulse"]
    
    t_start = 44
    t_end = 100
    
    cavity_dac_pulse = pulse_slice(t_start,t_end,cavity_dac_pulse)
    qubit_dac_pulse = pulse_slice(t_start,t_end,qubit_dac_pulse)

    suffix = "sliced"
    
    # Save file with today's date
    # save cavity dac pulse and qubit dac pulse separately for now
    date_str = datetime.datetime.now().strftime("%Y%d%m_%H%M%S_oct_pulse")
    filepath_cavity = OCT_PULSES_PATH / f"{cavity__load_path[:cav_len-5]}_{suffix}_{str(t_end)}"
    filepath_qubit = OCT_PULSES_PATH / f"{qubit__load_path[:cav_len-6]}_{suffix}_{str(t_end)}"
    print(f"{date_str}_qubit_{suffix}")
    np.savez(filepath_cavity, oct_pulse=cavity_dac_pulse)
    np.savez(filepath_qubit, oct_pulse=qubit_dac_pulse)

    # plotting the pulse
    t = np.linspace(0, len(cavity_dac_pulse), len(cavity_dac_pulse))
    w = 0.5
    fig, axs = plt.subplots(4, 1)
    axs[0].plot(np.real(cavity_dac_pulse))
    axs[0].plot(np.imag(cavity_dac_pulse))
    axs[1].plot(np.real(qubit_dac_pulse))
    axs[1].plot(np.imag(qubit_dac_pulse))
    axs[2].plot(
        np.cos(w * t) * np.real(cavity_dac_pulse)
        - np.sin(w * t) * np.imag(cavity_dac_pulse)
    )
    axs[2].plot(
        np.sin(w * t) * np.real(cavity_dac_pulse)
        + np.cos(w * t) * np.imag(cavity_dac_pulse)
    )
    axs[3].plot(
        np.cos(w * t) * np.real(qubit_dac_pulse)
        - np.sin(w * t) * np.imag(qubit_dac_pulse)
    )
    axs[3].plot(
        np.sin(w * t) * np.real(qubit_dac_pulse)
        + np.cos(w * t) * np.imag(qubit_dac_pulse)
    )
    plt.xlabel("ns")
