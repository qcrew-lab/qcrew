'''
Holds the functions for retrieving and saving the data
and for visualisation
Last Update: 10 Sept 2022 Kai Xiang
'''
import numpy as np
import matplotlib.pyplot as plt
from qutip import *
from get_pulse_seq import *

def save(result, save_path, args):
    '''
    To save relevant information
    '''
    np.savez(
        save_path,
        ts = result.ts
        cav_X = result.controls[0],
        cav_Y = result.controls[1],
        qb_X = result.controls[2],
        qb_Y = result.controls[3],
        chi = args['chi'],
        anharm = args['anharm'],
        kerr = 0 if 'kerr' not in args else args['kerr'],
        c_dims = 8 if 'c_dims' not in args else args['c_dims'],
        q_dims = 2 if 'q_dims' not in args else args['q_dims'],
        p_len = args['p_len'],
        name = None if 'name' not in args else args['name'],
        targ_fid = args['targ_fid']
    )

    print(f"File saved at {save_path}")

def read(read_path):
    args = dict()
    return None

def show_pulse(result):
    '''
    Plotting the Pulse waveform
    '''
    plt.plot(result.ts, result.controls[0], label = "Resonator Pulse X")
    plt.plot(result.ts, result.controls[1], label = "Resonator Pulse Y")
    plt.plot(result.ts, result.controls[2], label = "Qubit Pulse X")
    plt.plot(result.ts, result.controls[3], label = "Qubit Pulse Y")
    plt.legend()
    plt.grid()
    plt.title("Pulse Sequence in the Interaction Picture")
    plt.show()

def show_evolution(result, args):
    H, H_ctrl = make_Hamiltonian(arg)
    H_targ = make_unitary_target(arg)