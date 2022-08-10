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
    BatchOptimizer
)
from qcrew.measure.ECD_control.ECD_control.ECD_optimization.optimization_analysis import (
    OptimizationAnalysis, OptimizationSweepsAnalysis
)

#OCT_ROTATIONS_PATH = Path(__file__).resolve().parents[4] / "config/oct_rotations"
#OCT_PULSES_PATH = Path(__file__).resolve().parents[4] / "config/oct_pulses"

if __name__ == "__main__":

    # input target state and size of hilbert space to optimise
    Nc = 80
    Nq = 2
    alpha = 1.5
    psi_t = qt.tensor(qt.fock(Nq, 0), (qt.coherent(
        Nc, alpha)+qt.coherent(Nc, -alpha)).unit())

    opt_params = {
        'N_blocks': 4,  # circuit depth
        # Batch size (number of circuit optimizations to run in parallel)
        'N_multistart': 200,
        'epochs': 100,  # number of epochs before termination
        'epoch_size': 10,  # number of adam steps per epoch
        'learning_rate': 0.02,  # adam learning rate
        'term_fid': 0.999,  # terminal fidelitiy
        'dfid_stop': 1e-2,  # stop if dfid between two epochs is smaller than this number
        'beta_scale': 3.0,  # maximum |beta| for random initialization
        # qubit tensor oscillator, start in |g> |0>
        'initial_states': [qt.tensor(qt.fock(Nq, 0), qt.fock(Nc, 0))],
        'target_states': [psi_t],  # end in |g> or |e> |target>.
        'name': 'identity',  # name for printing and saving
        # if no filename specified, results will be saved in this folder under 'name.h5'
        'filename': None,
    }
    opt = BatchOptimizer(**opt_params)
    opt.optimize()
    best_circuit = opt.best_circuit()

    # user defined suffix to append to file saving the oct pulse
    suffix = ""

    # path to the .npz file containing rotation params or directly from simulator
    #path = OCT_ROTATIONS_PATH / "fock_states/fock3.npz"
    betas = best_circuit['betas']
    phis = best_circuit['phis']
    thetas = best_circuit['thetas']

    # enter your circuit Hamiltonian parameters for each mode
    # here, we have a storage cavity and a qubit
    storage_params = {
        "chi_kHz": 250,  # dispersive shift in kHz
        "chi_prime_Hz": 0,  # second order dispersive shift in Hz
        "Ks_Hz": 0,  # Kerr correction not yet implemented.
        # largest oscillator drive amplitude in MHz (max|epsilon|)
        "epsilon_m_MHz": 400,
        # DAC unit amp of gaussian displacement to alpha=1.
        "unit_amp":  0.1349*0.2,
        "sigma": 16,  # oscillator displacement sigma
        # oscillator displacement chop (number of stds. to include in gaussian pulse)
        "chop": 6,
    }
    qubit_params = {
        "unit_amp": 1.5846*0.2,
        "sigma": 40,
        "chop": 6,
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
