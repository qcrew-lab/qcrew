""" Script that generates OCT pulse after you give it rotations """

import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ECD_control.ECD_pulse_construction.ECD_pulse_construction import (
    FakeQubit,
    FakeStorage,
    conditional_displacement_circuit,
)

OCT_ROTATIONS_PATH = Path.cwd() / "config/oct_rotations"
OCT_PULSES_PATH = Path.cwd() / "config/oct_pulses"

if __name__ == "__main__":

    # user defined suffix to append to file saving the oct pulse
    suffix = "_"

    # path to the .npz file containing rotation params
    path = OCT_ROTATIONS_PATH / ""
    betas = np.load(path)["betas"]
    phis = np.load(path)["phis"]
    thetas = np.load(path)["thetas"]

    # enter your circuit Hamiltonian parameters for each mode
    # here, we have a storage cavity and a qubit
    storage_params = {
        "chi_kHz": 33,  # dispersive shift in kHz
        "chi_prime_Hz": 1,  # second order dispersive shift in Hz
        "Ks_Hz": 0,  # Kerr correction not yet implemented.
        "epsilon_m_MHz": 400,  # largest oscillator drive amplitude in MHz (max|epsilon|)
        "unit_amp": 0.01,  # DAC unit amp of gaussian displacement to alpha=1.
        "sigma": 11,  # oscillator displacement sigma
        "chop": 4,  # oscillator displacement chop (number of stds. to include in gaussian pulse)
    }
    qubit_params = {
        "unit_amp": 0.5,
        "sigma": 6,
        "chop": 4,
    }

    # set the maximum displacement used during the ECD gates
    alpha_CD = 30

    # small delay to insert between oscillator and qubit pulses
    buffer_time = 4

    # create a "Fake storage" and "Fake qubit"
    storage = FakeStorage(**storage_params)
    qubit = FakeQubit(**qubit_params)

    # generating the conditional displacement circuit.
    # set 'chi_prime_correction = True' to correct for linear part of chi'
    # #final_disp = True will implement final ECD gate as a displacement

    pulse_dict = conditional_displacement_circuit(
        betas,
        phis,
        thetas,
        storage,
        qubit,
        alpha_CD,
        buffer_time=buffer_time,
        kerr_correction=False,
        chi_prime_correction=True,
        final_disp=True,
        pad=True,
    )

    cavity_dac_pulse, qubit_dac_pulse, = (
        pulse_dict["cavity_dac_pulse"],
        pulse_dict["qubit_dac_pulse"],
    )

    # Save file with today's date
    date_str = datetime.datetime.now().strftime("%Y%d%m_%H%M%S_oct_pulse")
    filepath = OCT_PULSES_PATH / date_str / suffix
    np.savez(filepath, cavity=cavity_dac_pulse, qubit=qubit_dac_pulse)

    # plotting the pulse
    fig, axs = plt.subplots(2, 1)
    axs[0].plot(np.real(cavity_dac_pulse))
    axs[0].plot(np.imag(cavity_dac_pulse))
    axs[1].plot(np.real(qubit_dac_pulse))
    axs[1].plot(np.imag(qubit_dac_pulse))
    plt.xlabel("ns")
