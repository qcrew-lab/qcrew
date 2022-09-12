from pygrape import *
from qutip import *

import numpy as np
import matplotlib.pyplot as plt

import os
from .data_control import get_AW_envelope
from matplotlib.animation import FuncAnimation

#######################################
########### Plotting Scripts ##########
#######################################
def show_pulse(result, title, fullpath = None):
    '''
    A function to show the pulse envelope

    Parameters
    -----------
    result : pygrape result obj
        The result from pygrape optimisation
    '''
    plt.plot(result.ts, result.controls[0],)
    plt.title(title)

    if fullpath is not None:
        plt.savefig(fullpath)
    
    plt.show()

def make_wigner_anim(H0, Hc, dims, result, fullpath):
    '''
    Make the wigner animation gif using the given parameters

    Parameters
    -----------
    H : List of Qobj
        Contains [Drift Hamiltonian, [Control Hamiltonian, amplitude function]]

    name: string
        Where to save the image, e.g., "anim.gif"
    '''
    t_list = np.arange(0, 1000, 0.1)

    initial = fock(dims,0)

    envelope = get_AW_envelope(result.controls[0], result.ts)
    Qubit_pulse = [Hc, envelope]
    H = [H0, Qubit_pulse]

    solved = mesolve(H, initial, t_list, options = Options(nsteps = 2000))

    b = destroy(dims)
    qubit_expectation = [(state.dag() * b.dag()*b * state)[0,0] for state in solved.states ]

    # plot wigner function
    max_range = 6
    displ_array = np.linspace(-max_range, max_range, 61)
    wigner_list0 = [wigner(x.ptrace(0), displ_array, displ_array) for x in solved.states[::40]]

    # create first plot
    fig, axes = plt.subplots(1,1)
    fig.set_size_inches(10, 8)
    wigner_f0 = wigner(solved.states[0].ptrace(0), displ_array, displ_array)
    cont0 = axes.pcolormesh(displ_array, displ_array, wigner_f0, cmap = "bwr")
    cb = fig.colorbar(cont0)

    # refresh function
    def animated_wigner(frame):
        wigner_f0 = wigner_list0[frame]
        cont0 = axes.pcolormesh(displ_array, displ_array, wigner_f0, cmap = "bwr")
        cont0.set_clim(-1/np.pi, 1/np.pi)

        axes.set_title("Qubit State", fontsize = 20)

    anim = FuncAnimation(fig, animated_wigner, frames=len(wigner_list0), interval=100)
    
    anim.save(os.path.join(fullpath), writer='imagemagick')

#######################################
########### Save Function #############
#######################################

def save(result, save_path,):
    '''
    To save relevant information
    Parameters
    ---------
    result : pygrape result object
        Describes the result of optimsation
    save_path : string
        Desribes the directory to save the file (.npz)
    
    Returns
    ---------
    None
    '''
    
    np.savez(
        save_path,
        ts = result.ts,
        pulseX = result.controls[0],
        pulseY = [] if len(result.controls) == 1 else result.controls[1],
    )