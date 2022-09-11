'''
This script is to get the pulse sequence given the input parameters
Last Update: 10 Sept 2022 Kai Xiang
'''

from pygrape import *
from qutip import *

def make_Hamiltonian(args):
    '''
    A function that creates the interaction Hamiltonian and the control drives

    Parameters
    ---------
    args : dict
        Contains the needed parameters for the simulation to run (in GHz)
        'chi'      : cross-Kerr term / dispersive shift ~ MHz range
        'Kerr'     : self-Kerr term for cavity          ~ 10 kHz range
        'anharm'   : qubit anharmonicity                ~ 100 MHz range
        'pulse_len': number of numerical time steps to use
        'c_dims'   : Number of Fock states before truncating
        'q_dims'   : Number of circuit levels (usually 2 or 3)
        'qubit drive'  : Initial amplitude of qubit drive
        'cavity drive' : Initial ampltide of cavity drive
        ... and other stuff
    
    Returns
    ---------
    H : Qobj
        Hamiltonian for system in Interaction picture
    H_ctrl: List of Qobj 
        Hamiltonians for drive terms
    '''

    chi = args['chi']
    anharm = args['anharm']
    kerr = 0 if 'kerr' not in args else args['kerr']
    Dq = 5e-3 *2 if 'qubit drive' not in args else args['qubit drive']
    Dc = 5e-3 *2 if 'cavity drive' not in args else args['cavity drive']

    Dq *= 2*np.pi
    Dc *= 2*np.pi

    c_dims = 8 if 'c_dims' not in args else args['c_dims']
    q_dims = 2 if 'q_dims' not in args else args['q_dims']

    c = tensor(destroy(c_dims), qeye(q_dims))
    q = tensor(qeye(c_dims), destroy(q_dims))
    cd = c.dag()
    qd = q.dag()

    H = cd*c*qd*q * chi         *2 * np.pi
    H += cd*cd*c*c * kerr/2     *2 * np.pi
    H += qd*qd*q*q * anharm/2   *2 * np.pi

    H_ctrl = [
        Dq * (q + qd),
        Dq * 1j*(q - qd),
        Dc * (c + cd),
        Dc * 1j*(c + cd),
    ]

    return H, H_ctrl


def make_unitary_target(arg):
    '''
    A function that creates the target unitary

    Parameters
    ---------
    arg : dict
        'name'     : For predetermined unitaries
        'unitary'  : For preset unitary
        'c_dims'   : Number of Fock states before truncating
        'q_dims'   : Number of circuit levels (usually 2 or 3)
        ... and other stuff

    Return
    ---------
    U : Qobj
        Unitary matrix describing the goal evolution
    '''
    
    U = None if 'unitary' not in arg else arg['unitary']

    if type(U) is Qobj:
        if U.check_isunitary():
            return U
        else:
            raise Exception("Qbj Operator is not unitary")

    name = None if 'name' not in arg else arg['name']
    c_dim = 8 if 'c_dims' not in arg else arg['c_dims']
    q_dim = 2 if 'q_dims' not in arg else arg['q_dims']

    if name == 'fock1':
        rotation = fock(c_dim,0) * fock(c_dim,1).dag()
        rotation += fock(c_dim,1) * fock(c_dim,0).dag()
        rotation += sum(ket2dm(fock(c_dim, i)) for i in range(2, c_dim))
        
        U = tensor(rotation, qeye(q_dim))
        return U

    if name == 'pipulse':
        rotation = fock(q_dim,0) * fock(q_dim,1).dag()
        rotation += fock(q_dim,1) * fock(q_dim,0).dag()

        U = tensor(qeye(c_dim), rotation)
        return U
    
def make_setup(arg):
    '''
    A function to make the set up we will be using for the pygrape optimisation

    Parameters
    ---------
    arg : dict
        contains all the stuff for the other two functions
        ... and other stuff
    
    Returns
    ---------
    setups : list of UnitarySetUp
        Information for pygrape optimsation
    '''
    H, H_ctrl = make_Hamiltonian(arg)
    H_targ = make_unitary_target(arg)

    setup1 = UnitarySetup(H, H_ctrl, H_targ)

    new_arg = arg.copy()
    new_arg['c_dims'] += 1

    del H, H_ctrl, H_targ
    
    H, H_ctrl = make_Hamiltonian(new_arg)
    H_targ = make_unitary_target(new_arg)

    setup2 = UnitarySetup(H, H_ctrl, H_targ)

    setups = [setup1, setup2]

    return setups



