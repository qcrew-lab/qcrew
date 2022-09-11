'''
This code is meant to simulate the Hamiltonian of interest to
generate the appropriate pulse sequence using GRAPE. This pulse 
sequence will then be stored as a ".npz" file and converted to an
actual pulse using the numerical pulse receipe

Last Update: Sept 2022 Kai Xiang
'''

######################################################

import numpy as np
import matplotlib.pyplot as plt
from pygrape import run_grape, random_waves, UnitarySetup, make_amp_cost
from qutip import *
import os
from helper_functions.Hamiltonians import *
from helper_functions.data_control import *

# Path for the save files for the ".npz"
path = r'qcrew\qcrew\measure\grape_ocp\Saved Pulse Sequences'
# Name of the file to be saved
name = 'fock1'

# Input target unitary matrix and target fidelity here
# I'm going to load some precalibrated targets, but the intention
# is to be able to specify the unitary in qutip
U_targ = 'fock1'
targ_fid = 0.999

args = {
    # Number of dimensions to simulate, depends on target state 
    # E.g., Fock state n = 1 requires >6 photons
    'c_dims': 10,
    'q_dims': 3,
    # In GHz
    'chi'   : -1.5e-3 * 2,
    'kerr'  : 1e-5,
    'anharm': 0.4,
    # Other deets
    'name'  : U_targ,
    'p_len'   : 500//2,
    'targ_fid': targ_fid,
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
    init = random_waves(n_ctrls = 4, plen = args['p_len'], npoints = 15)

penalties = [make_amp_cost(1, 1, iq_pairs = True)]
opts = {
    'maxfun' : 15000 * 5,
    'maxiter': 15000 * 5,
    }

setups = make_setup(args)
result = run_grape(init, setups, term_fid = targ_fid, opts = opts, dt = 1)

save(result, fullpath, args)

show_pulse(pulse_save_file = fullpath)
show(pulse_save_file = fullpath)
show_evolution(pulse_save_file = fullpath, save_path = os.path.join(path, name + '.gif'))



