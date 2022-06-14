import numpy as np
from pygrape import run_grape, UnitarySetup, get_unitary, plot_matrix

H = np.array([
    [0, 0],
    [0, 1],
])
Hc_x = np.array([
    [0, 1],
    [1, 0],
])
Hc_y = np.array([
    [0,  1j],
    [-1j, 0],
])
U_target = np.array([
    [1,  1],
    [1, -1],
]) / np.sqrt(2)
gauge_op = np.array([
    [1,  0],
    [0, -1],
])

setup = UnitarySetup(H, [Hc_x, Hc_y], U_target, [gauge_op])
init_ctrls = 1e-3 * np.ones((2, 200))

result = run_grape(init_ctrls, setup, dt=.2, init_aux_params=[0])

import matplotlib.pyplot as plt
U = get_unitary(result.controls, H, [Hc_x, Hc_y], dt=.2)
fig, axes = plt.subplots(1, 2)
plot_matrix(U_target, ax=axes[0], labels=('g', 'e'))
plot_matrix(U / np.exp(1j*np.angle(U[0,0])), ax=axes[1], labels=('g', 'e'))
axes[0].set_title('Target')
axes[1].set_title('Optimized')
plt.tight_layout()
plt.savefig('../docs/_static/pi_2_pulse_gauge_prop.png')
plt.show()
