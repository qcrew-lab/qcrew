import numpy as np
from pygrape import *

out_dir = "C:/Users/qcrew/Desktop/qcrew/qcrew/config/oct_pulses"

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
reporters = [
    print_costs(),
    save_waves(["qI", "qQ"], 5),
    plot_waves(["qI", "qQ"], 5),
    # plot_trajectories(setups[0], 10),
    # plot_states(10),
    # plot_fidelity(10),
    #verify_from_setup(make_setup(c_dim + 2, q_dim), 10),
]

result = run_grape(init_ctrls, setup, reporter_fns=reporters, dt=.2, outdir=out_dir, save_data=1, term_fid=0.999)

import matplotlib.pyplot as plt
plt.plot(result.ts, result.controls[0])
# plt.savefig('../docs/_static/pi_pulse_ctrls.png')
plt.show()