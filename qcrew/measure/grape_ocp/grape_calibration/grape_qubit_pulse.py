"""
This script will find the optimal pulse for a qubit control pulse
For both pi-pulse and pi/2-pulse

Last Update: Sept 2022 Kai Xiang
"""

from qcrew.measure.grape_ocp.grape.grape.pygrape import *
from qutip import *

import numpy as np
import matplotlib.pyplot as plt

from qcrew.measure.grape_ocp.helper_functions.qubit_pulse_helper import *

# from helper_functions.qubit_pulse_helper import *

#######################################
##### Setting Up the Hamiltonian ######
#######################################

b = destroy(2)

H0 = b.dag() * b
Hc = 1j*(b.dag() - b)

###### Defining Gate Operation ########

U_target = b.dag() + b
name = "π_Pulse_Y"

############ Set-up Grape ############

setup = UnitarySetup(H0, [Hc], U_target)
init_ctrls = 1e-3 * np.ones((1, 200))

penalties = [make_amp_cost(1, 1, iq_pairs=True)]
opts = {
    "maxfun": 15000 * 5,
    "maxiter": 15000 * 5,
}
result = run_grape(init_ctrls, setup, dt=0.2)

path = "C:\\Users\\qcrew\\Desktop\\qcrew\\qcrew\\qcrew\\measure\\grape_ocp\\Saved Pulse Sequences\\"

save(result, path + name + ".npz")
show_pulse(result, path + name + ".png")
make_wigner_anim(H0, Hc, 2, result, path + name + ".gif")
