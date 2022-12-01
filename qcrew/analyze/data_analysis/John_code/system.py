"""
This file builds the system on which our algos are run. It includes numerical parameters as the dimension, Operators and parameters

The Hilbertspace is constructed as
tensor(qubit, cavity)

I am using the convention a = X + iP -> use g = 2 in wigner

Units are in MHz - mus

Note: If change are made here, the interactive consolte has to be restarted to carry them over.


"""
import qutip as qt
from qutip.qip.operations import rx, ry, rz
import numpy as np


N = 120
# System parameters
CHI = 2 * np.pi * 0.04  # crosskerr

# CHI = 2*np.pi*0.04 # crosskerr

KERR = 2 * np.pi * 0  # cavity selfkerr
EPSILON = 70  # default drive

T1Q = 0
T2Q = 0
T1C = 0

# Identity Operators
Ic = qt.qeye(N)
Iq = qt.qeye(2)

# Projectors
proj_g = qt.tensor(qt.fock(2, 0) * qt.fock(2, 0).dag(), Ic)
proj_e = qt.tensor(qt.fock(2, 1) * qt.fock(2, 1).dag(), Ic)

# Qubit Operators
sx = qt.tensor(qt.sigmax(), Ic)
sy = qt.tensor(qt.sigmay(), Ic)
sz = qt.tensor(qt.sigmaz(), Ic)


def Rx(theta):
    return qt.tensor(rx(theta), Ic)


def Ry(theta):
    return qt.tensor(ry(theta), Ic)


def Rz(theta):
    return qt.tensor(rz(theta), Ic)


# Cavity Operators
a = qt.tensor(Iq, qt.destroy(N))

# Hamiltonians
## Dispersive
def H_dispersive(chi=CHI):
    return -chi / 2 * a.dag() * a * sz


## Dispersive with Drive
# I added the 1j factor such that it is consistent with qt.displace and coheren(N,alpha)
def H_dispersiveDrive(chi=CHI, epsilon=EPSILON):
    return -chi / 2 * a.dag() * a * sz + (
        1j * epsilon * a.dag() + np.conjugate(1j * epsilon) * a
    )


# def H_dispersiveDrive(chi=CHI, epsilon = EPSILON):
#     return -chi/2*a.dag()*a*sz + (epsilon*a.dag() + np.conjugate(epsilon)*a)

# Define States
vac = qt.tensor(qt.fock(2, 0), qt.fock(N, 0))
superpos = qt.tensor((qt.fock(2, 0) + qt.fock(2, 1)).unit(), qt.fock(N, 0))

# define loss


def calc_loss(cav_t1, cav_t2, q_t1, q_t2):

    gamma_a_loss = 1 / cav_t1
    gamma_a_daphasing = 1 / cav_t2
    gamma_q_dacay = 1 / q_t1
    gamma_q_dephasing = 1 / q_t2

    a_loss = np.sqrt(gamma_a_loss) * a
    a_dephasing = np.sqrt(gamma_a_daphasing) * (a * a.dag() + a.dag() * a)
    q_dacay = np.sqrt(gamma_q_dacay) * (sx + 1j * sy) / 2
    q_dephasing = np.sqrt(gamma_q_dephasing) * sz

    return a_loss, a_dephasing, q_dacay, q_dephasing


LOSS = calc_loss(np.inf, np.inf, np.inf, np.inf)


U_phase_error = {
    "phase_error_U1": 0,
    "phase_error_U2": 0,
    "phase_error_U3": 0,
}

V_phase_error = {
    "phase_error_V1": 0,
    "phase_error_V2": 0,
    "phase_error_V3": 0,
}

displace_phase_error = 0
