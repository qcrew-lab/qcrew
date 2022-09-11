'''
This script will find the optimal pulse for a qubit pi-pulse

Last Update: Sept 2022 Kai Xiang
'''

from pygrape import *
from qutip import *

import numpy as np
import matplotlib.pyplot as plt
import os
from data_control import *

def make_Hamiltonian(args):
    '''
    A function that creates the interaction Hamiltonian and the control drives

    Parameters
    ---------
    args : dict
        Contains the needed parameters for the simulation to run (in GHz)
        'pulse_len': number of numerical time steps to use
        'qubit drive'  : Initial amplitude of qubit drive
        'cavity drive' : Initial ampltide of cavity drive
        'qubit_freq'   : Qubit frequency
        ... and other stuff
    
    Returns
    ---------
    H : Qobj
        Hamiltonian for system in Interaction picture
    H_ctrl: List of Qobj 
        Hamiltonians for drive terms
    '''

    Dq = 5e-3 *2 if 'qubit drive' not in args else args['qubit drive']
    Dc = 5e-3 *2 if 'cavity drive' not in args else args['cavity drive']

    Dq *= 2*np.pi
    Dc *= 2*np.pi
    q_freq = args['qubit_freq']

    q = destroy(2)
    qd = q.dag()
    
    H = qd * q


    H_ctrl = [
        Dq * (q + qd),
        Dq * 1j*(qd - q),
    ]

    return H, H_ctrl

def make_unitary_target():
    '''
    A function that creates the target unitary (pi-pulse)

    Return
    ---------
    U : Qobj
        Unitary matrix describing the goal evolution
    '''
    
    return fock(2,0)*fock(2,1).dag() + fock(2,1)*fock(2,0).dag()

def find_pulse():
    # Path for the save files for the ".npz"
    path = r'qcrew\qcrew\measure\grape_ocp\Saved Pulse Sequences'
    # Name of the file to be saved
    name = 'pi_pulse1'

    args = {
        # In GHz
        'qubit_freq' : 5.5,
        # Other deets
        'name'  : 'pi-pulse',
        'p_len'   : 500//2,
        'targ_fid': 0.999,
    }

    fullpath = os.path.join(path, name + '.npz')
    init = None

    if os.path.exists(fullpath):
        '''
        Insert a way to convert the .npz file into the starting initial pulse shape
        '''
        saved_ts, saved_amps, saved_args = read_amplitudes_from_file(fullpath)
        print("Path Found!")
        init = saved_amps
    else:
        init = random_waves(n_ctrls = 2, plen = args['p_len'], npoints = 15)

    penalties = [make_amp_cost(1, 1, iq_pairs = True)]
    opts = {
        'maxfun' : 15000 * 5,
        'maxiter': 15000 * 5,
        }

    setups = StateTransferSetup(*make_Hamiltonian(args), [fock(2,0)], [fock(2,1)])
    
    result = run_grape(init, setups, term_fid = args['targ_fid'], opts = opts, dt = 1)

    save(result, fullpath, args)

    show_pulse(pulse_save_file = fullpath)
    show(pulse_save_file = fullpath)
    #show_evolution(pulse_save_file = fullpath, save_path = os.path.join(path, name + '.gif'))



find_pulse()
