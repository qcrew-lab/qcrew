from qutip import destroy, basis, coherent
from pygrape import *

d = 35
PLEN = 200

a = destroy(d)
ad = a.dag()
a3 = a*a*a
a3d = a3.dag()
H0 = np.zeros((d, d), dtype=complex)

# Avoid truncation issues by penalizing reaching the boundary
# Since the control hamiltonians couple terms 3 number states away
# impose an effective loss of norm for visiting any of the last 3 states
H0[d-3, d-3] = H0[d-2, d-2] = H0[d-1, d-1] = -1j

Hcs = [
    a + ad,   1j*(a - ad),
    a3 + a3d, 1j*(a3 - a3d),
]

def cat(a):
    return (coherent(d, a) + coherent(d, -a)).unit()

inits = [basis(d, 0)]
finals = [cat(1.4)]
setup = StateTransferSetup(H0, Hcs, inits, finals)

init_ctrls = 1e-4 * np.ones((4, PLEN))
penalties = [make_deriv_cost(1e-4, .01)]

result = run_grape(init_ctrls, setup, penalty_fns=penalties, ftol=1e-5)

import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 1, sharex=True)
axes[0].plot(result.ts, result.controls[0], label='I')
axes[0].plot(result.ts, result.controls[1], label='Q')
axes[0].legend()
axes[0].set_title(r'$a + a^\dagger$')
axes[1].plot(result.ts, result.controls[2], label='I')
axes[1].plot(result.ts, result.controls[3], label='Q')
axes[1].legend()
axes[1].set_title(r'$a^3 + (a^\dagger)^3$')
# plt.savefig('../docs/_static/a_cubed_ctrls.png')
plt.show()

