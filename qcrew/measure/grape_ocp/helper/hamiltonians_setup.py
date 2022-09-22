from qcrew.qcrew.measure.grape_ocp.grape.grape.pygrape import *
from qutip import*

def make_Hamiltonian(cdim, qdim, anharm = -0.0378, kerr = -0e-6, chi = -0.6e-3, cdrive = 1, qdrive = 1):
    '''
    A function to create the drift Hamiltonian for a qubit-cavity system

    Parameters
    --------------
    cdim : int
        Truncation for Fock levels

    qdim : int
        Dimensions of qubit (or qutrit)

    anharm : float
        Anharmonicity/self-Kerr of qubit in  GHz

    kerr : float
        Anharmonicity/self-Kerr of cavity in GHz

    chi : float
        First-order Cross-Kerr of qubit-cavity in  GHz

    Returns
    -----------
    H0 : QObj
        Drift Hamiltonian for the system

    Hc : List(QObj, ... )
        List of control Hamiltonians for the system
    '''
    q = tensor(qeye(cdim), destroy(qdim))
    qd = q.dag()
    c = tensor(destroy(cdim), qeye(qdim))
    cd = c.dag()

    # Hamiltonian
    H0 =  anharm * qd*qd*q*q
    H0 += kerr * cd*cd*c*c
    H0 += chi *cd*c*qd*q

    # Control Hamiltonians
    Hc = [
        2*np.pi*(c + cd)*cdrive,
        1j*2*np.pi*(c - cd)*cdrive,
        2*np.pi*(q + qd)*qdrive,
        1j*2*np.pi*(q - qd)*qdrive,
        ]

    return H0, Hc


        









