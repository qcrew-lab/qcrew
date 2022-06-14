import numpy as np
from pygrape import run_grape, UnitarySetup

H = np.array([
    [0, 0],
    [0, 1],
])
Hc = np.array([
    [0, 1],
    [1, 0],
])
U_target = np.array([
    [0, 1],
    [1, 0],
])
setup = UnitarySetup(H, [Hc], U_target)
init_ctrls = 1e-3 * np.ones((1, 200))

result = run_grape(init_ctrls, setup, dt=.2)

import matplotlib.pyplot as plt
plt.plot(result.ts, result.controls[0])
# plt.savefig('../docs/_static/pi_pulse_ctrls.png')
plt.show()