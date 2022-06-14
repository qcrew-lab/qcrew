import numpy as np
from pygrape import run_grape, UnitarySetup, make_amp_cost

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

penalties = [make_amp_cost(1e-5, 0.05, iq_pairs=True)]
result = run_grape(init_ctrls, setup, penalty_fns=penalties, dt=.2)

import matplotlib.pyplot as plt
controls = result.controls[0] + 1j*result.controls[1]
plt.plot(result.ts, controls.real, label='x')
plt.plot(result.ts, controls.imag, label='y')
plt.plot(result.ts, abs(controls), label='abs')
plt.legend()
# plt.savefig('../docs/_static/pi_pulse_bounded_ctrls.png')
plt.show()
