'''
This code is meant to simulate the Hamiltonian of interest to
generate the appropriate pulse sequence using GRAPE. This pulse 
sequence will then be stored as a ".npz" file and converted to an
actual pulse using the numerical pulse receipe
'''

######################################################
########### import YALE's pygrape ####################
######################################################

from setuptools import setup

setup(
    name='pygrape',
    version='0.1',
    packages=['pygrape'],
    url='https://git.yale.edu/RSL/grape',
    license='MIT',
    author='Phil Reinhold',
    author_email='philip.reinhold@yale.edu',
    description='GRAPE Optimal Control'
)

######################################################

import numpy as np
import matplotlib.pyplot as plt
from pygrape import run_grape, random_waves, UnitarySetup, make_amp_cost
import sim_helper_functions as sim
from qutip import *

# Number of dimensions to simulate, depends on target state
fock_dims = 8
qubit_dims = 3

# Input system parameters here (in GHz)
chi = 1.5e-3 * 2
kerr = 1e-5
anharm = 0.4





