import numpy as np
from pygrape import run_grape, StateTransferSetup
from pygrape.grape import get_impulse_response
import qutip

dim = 3
anharm = 114.5e-3
a = qutip.destroy(dim)
ad = a.dag()
H = (anharm/2) * ad * ad * a * a
Hc_x = a + ad
Hc_y = 1j*(a - ad)
init_states = [
    qutip.basis(dim, 0),
    qutip.basis(dim, 1),
]
final_states = [
    qutip.basis(dim, 1),
    qutip.basis(dim, 0),
]

setup = StateTransferSetup(H, [Hc_x, Hc_y], init_states, final_states)
init_ctrls = 1e-3 * np.ones((2, 20))


# 4th order 300MHz Butterworth low-pass filter
filt_func = lambda f: 1 / np.sqrt(1 + (f / .3)**8)
dt = 1    # 1 ns resolution on AWG
n_ss = 20 # We'll subsample that by a factor of 20
          # so the simulation resolution will be 50 ps

result = run_grape(init_ctrls, setup, dt=1, n_ss=20, filt_func=filt_func, shape_sigma=1)

import matplotlib.pyplot as plt
fig, axes = plt.subplots(3, 1, sharex=True)
ts = np.arange(len(result.controls[0])) / float(n_ss)
awg_ctrls = np.kron(result.awg_controls, np.ones(n_ss))
axes[0].plot(ts[:len(awg_ctrls[0])], awg_ctrls[0], label='x-AWG')
axes[0].plot(ts[:len(awg_ctrls[0])], awg_ctrls[1], label='y-AWG')
axes[0].legend()
axes[1].plot(ts, result.controls[0], label='x-out')
axes[1].plot(ts, result.controls[1], label='y-out')
axes[1].legend()
axes[2].plot(ts[:len(result.response)], result.response, label='Impulse Response')
axes[2].legend()
# plt.savefig('../docs/_static/pi_pulse_subsample.png')
plt.show()