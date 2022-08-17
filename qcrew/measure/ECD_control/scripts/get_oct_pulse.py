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
)
from qcrew.measure.ECD_control.ECD_control.ECD_optimization.batch_optimizer import (
    BatchOptimizer,
)

# OCT_ROTATIONS_PATH = Path(__file__).resolve().parents[4] / "config/oct_rotations"
OCT_PULSES_PATH = Path(__file__).resolve().parents[4] / "config/oct_pulses"

if __name__ == "__main__":

    # input target state and size of hilbert space to optimise
    Nc = 60
    Nq = 2
    alpha = 1
    psi_t = qt.tensor(
        qt.fock(Nq, 0), (qt.squeeze(Nc, 1) * qt.coherent(Nc, alpha)).unit()
    )

    opt_params = {
        "N_blocks": 3,
        "N_multistart": 200,
        "epochs": 100,
        "epoch_size": 10,
        "learning_rate": 0.03,
        "term_fid": 0.999,
        "dfid_stop": 1e-2,
        "beta_scale": 3.0,
        "initial_states": [qt.tensor(qt.fock(Nq, 0), qt.fock(Nc, 0))],
        "target_states": [psi_t],
        "name": "identity",
        "filename": None,
    }
    opt = BatchOptimizer(**opt_params)
    opt.optimize()
    best_circuit = opt.best_circuit()

    # user defined suffix to append to file saving the oct pulse
    suffix = ""

    # path to the .npz file containing rotation params or directly from simulator
    # path = OCT_ROTATIONS_PATH / "fock_states/fock3.npz"
    # betas = np.load(path)["betas"]
    # phis = np.load(path)["phis"]
    # thetas = np.load(path)["thetas"]

    # load directly from optimizer
    betas = best_circuit["betas"]
    phis = best_circuit["phis"]
    thetas = best_circuit["thetas"]

    # enter your circuit Hamiltonian parameters for each mode
    # here, we have a storage cavity and a qubit
    pulse_shape = "Cosine"
    storage_params = {
        "chi_kHz": 45,  # dispersive shift in kHz
        "chi_prime_Hz": 0,  # second order dispersive shift in Hz
        "Ks_Hz": 0,  # Kerr correction not implemented here.
        "unit_amp": 0.0572,  # DAC amplitude (at maximum of pulse) for gaussian displacement to alpha=1.
        "sigma": 8,  # oscillator displacement pulse sigma
        "chop": 6,  # oscillator displacement pulse chop (number of sigmas to include in gaussian pulse)
        "length_ring": 8,
        "length_constant": 40,
        "pulse_shape": pulse_shape,
    }

    qubit_params = {
        "unit_amp": 1.839,
        "sigma": 8,
        "chop": 6,
        "length_ring": 8,
        "length_constant": 20,
        "pulse_shape": pulse_shape,
    }  # parameters for qubit pi pulse.

    # set the maximum displacement used during the ECD gates
    alpha_CD = 10

    # small delay to insert between oscillator and qubit pulses
    buffer_time = 0

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
        pulse_shape=pulse_shape,
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
    # save cavity dac pulse and qubit dac pulse separately for now
    date_str = datetime.datetime.now().strftime("%Y%d%m_%H%M%S_oct_pulse")
    filepath_cavity = OCT_PULSES_PATH / f"{date_str}_cavity_{suffix}"
    filepath_qubit = OCT_PULSES_PATH / f"{date_str}_qubit_{suffix}"
    np.savez(filepath_cavity, oct_pulse=cavity_dac_pulse)
    np.savez(filepath_qubit, oct_pulse=qubit_dac_pulse)

    # plotting the pulse
    fig, axs = plt.subplots(2, 1)
    axs[0].plot(np.real(cavity_dac_pulse))
    axs[0].plot(np.imag(cavity_dac_pulse))
    axs[1].plot(np.real(qubit_dac_pulse))
    axs[1].plot(np.imag(qubit_dac_pulse))
    plt.xlabel("ns")
