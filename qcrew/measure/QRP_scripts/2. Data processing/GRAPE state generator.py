import numpy as np
from qutip import *
from pathlib import Path
"""
This file gets a folder of GRAPE pulses and simulate the expected final states 
"""

# Grape pulses
grape_directory = r"C:\Users\qcrew\Desktop\qcrew\qcrew\config\GRAPE\clara-grape"
save_simulated_state = True
states_directory = r"C:\Users\qcrew\Desktop\qcrew\qcrew\config\GRAPE\GRAPE states n=0"

# Simulation Dimensions
cdim = 30
qdim = 3

# Define  meanthermal excitation
nbar_cav = 0.00 
nbar_qb = 0.0  # we using pre-selection!

# Hamiltonian Parameters in GHz
chi = 1.359e-3
Kerr = 6e-6
alpha = 175.65e-3

# Coherences in ns
T1 = 84e3
T2 = 24e3
Tphi = 1 / (1 / T2 - 0.5 / T1)
cavT1 = 1.21e6
# cavT2 = 1.34e6#2*cavT1

# Preliminaries
pi = np.pi

# Mode Operators
q = destroy(qdim)
c = destroy(cdim)
qd, cd = q.dag(), c.dag()

Q = tensor(q, qeye(cdim))
C = tensor(qeye(qdim), c)
Qd, Cd = Q.dag(), C.dag()

# Initial State
initial = tensor(thermal_dm(qdim, nbar_qb), thermal_dm(cdim, nbar_cav))

# Collapse Operators
c_ops = [
    np.sqrt((1 + nbar_qb) / T1) * Q,  # Qubit Relaxation
    np.sqrt(nbar_qb / T1) * Qd,  # Qubit Thermal Excitations
    np.sqrt(2 / Tphi) * Qd * Q,  # Qubit Dephasing
    np.sqrt((1 + nbar_cav) / cavT1) * C,  # Cavity Relaxation
    np.sqrt(nbar_cav / cavT1) * Cd,  # Cavity Thermal Excitations
]

# Drift Hamiltonian
H0 = (
    -2 * pi * chi * Cd * C * Qd * Q
    - 2 * pi * Kerr / 2 * Cd * Cd * C * C
    - 2 * pi * alpha / 2 * Qd * Qd * Q * Q
)

selection = []
for file in Path(grape_directory).glob("*"):
    selection.append(file.stem)


def target_state(name):
    if len(name) == 5:  # fock0, fock1, fock2...
        target = fock(cdim, int(name[-1]))
        return target

    elif len(name) == 6:  # fock01, fock02, fock34...
        target = (fock(cdim, int(name[-2])) + fock(cdim, int(name[-1]))).unit()
        return target

    elif len(name) == 7:  # fock0i1, fock0i2, fock3i4...
        target = (fock(cdim, int(name[-3])) + 1j * fock(cdim, int(name[-1]))).unit()
        return target

    else:
        print("State ", name, "invalid!")
        pass


def drive_amp(t, dt, drive):
    """Returns the drive amplitude for a given time"""
    drive_index = int(t // dt)

    if drive_index == len(cavQ):
        drive_index -= 1

    return drive[drive_index]


for name in selection:
    target = target_state(name)
    data = np.load(grape_directory + "/" + name + ".npz", "r")

    dt = data["dt"]
    qubitI = data["QubitI"]
    qubitQ = data["QubitQ"]
    cavI = data["CavityI"]
    cavQ = data["CavityQ"]

    tlist = [dt * i for i in range(len(cavQ))]

    H_drive = [
        [2 * pi * (Q + Qd), lambda t, *args: drive_amp(t, dt, qubitI)],
        [2j * pi * (Q - Qd), lambda t, *args: drive_amp(t, dt, qubitQ)],
        [2 * pi * (C + Cd), lambda t, *args: drive_amp(t, dt, cavI)],
        [2j * pi * (C - Cd), lambda t, *args: drive_amp(t, dt, cavQ)],
    ]

    H = [H0, *H_drive]

    # Dynamics
    options = Options(max_step=2, nsteps=1e6)
    results = mesolve(
        H,
        initial,
        tlist,
        c_ops=c_ops,
        options=options,
    )  # progress_bar= True)

    if save_simulated_state:
        np.savez(states_directory + "/" + name + ".npz", rho=results.states[-1])

    cav_state = results.states[-1].ptrace(1)  # .tidyup(1e-2)
    qubit_state = results.states[-1].ptrace(0)  # .tidyup(1e-2)

    F = np.round(fidelity(cav_state, target), 3)
    Pe = expect(fock_dm(qdim, 1), qubit_state)

    print("State", name, ": \n", "Fidelity: ", F, "\n", "Pe: ", Pe, "\n")