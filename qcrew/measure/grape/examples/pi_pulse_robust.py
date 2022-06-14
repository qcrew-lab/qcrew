import numpy as np
from pygrape import run_grape, UnitarySetup

def make_setup(detune):
    H = detune * np.array([
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
    return UnitarySetup(H, [Hc_x, Hc_y], U_target)

setups = [make_setup(detune) for detune in np.linspace(.97, 1.03, 12)]
init_ctrls = 1e-3 * np.ones((2, 200))

# Run using 4 processors. Will run 4 setups at a time
result = run_grape(init_ctrls, setups, dt=.2, n_proc=4)

import matplotlib.pyplot as plt
plt.plot(result.ts, result.controls[0], label='x')
plt.plot(result.ts, result.controls[1], label='y')
plt.legend()
# plt.savefig('../docs/_static/pi_pulse_robust_ctrls.png')
plt.show()
