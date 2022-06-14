import numpy as np
from pygrape import run_grape, UnitarySetup

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
    [0, 1],
    [1, 0],
])
setup = UnitarySetup(H, [Hc_x, Hc_y], U_target)
init_ctrls = 1e-3 * np.ones((2, 200))

result = run_grape(init_ctrls, setup, dt=.2)

import matplotlib.pyplot as plt
plt.plot(result.ts, result.controls[0], label='x')
plt.plot(result.ts, result.controls[1], label='y')
plt.legend()
# plt.savefig('../docs/_static/pi_pulse_xy_ctrls.png')
plt.show()
