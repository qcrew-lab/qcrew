import numpy as np
from pygrape import run_grape, StateTransferSetup
import qutip

dim = 5
anharm = .4
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
init_ctrls = 1e-3 * np.ones((2, 200))

result = run_grape(init_ctrls, setup, dt=.2)

import matplotlib.pyplot as plt
plt.plot(result.ts, result.controls[0], label='x')
plt.plot(result.ts, result.controls[1], label='y')
plt.legend()
# plt.savefig('../docs/_static/pi_pulse_state_transfer_ctrls.png')
plt.show()
