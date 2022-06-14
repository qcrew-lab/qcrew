import numpy as np
from pygrape import run_grape, StateTransferSetup
import qutip

q_dim = 2
c_dim = 10
pulse_len = 300

# In GHZ
anharm = .4
kerr = 1e-5
chi = 2e-3
drive = D = 2 * np.pi * 1e-3

def make_setup(c_dim, q_dim):
    a = qutip.tensor(qutip.destroy(c_dim), qutip.qeye(q_dim))
    b = qutip.tensor(qutip.qeye(c_dim), qutip.destroy(q_dim))
    ad = a.dag()
    bd = b.dag()
    H0 = (anharm/2) * bd * bd * b * b
    H0 += (kerr/2) * ad * ad * a * a
    H0 += (chi) * ad * a * bd * b
    H0 *= 2*np.pi
    Hcs = [D*(b + bd), 1j*D*(b - bd), D*(a + ad), 1j*D*(a - ad)]

    init_states = [
        qutip.tensor(qutip.basis(c_dim, 0), qutip.basis(q_dim, 0))
    ]

    final_states = [
        qutip.tensor(qutip.basis(c_dim, 1), qutip.basis(q_dim, 0))
    ]

    return StateTransferSetup(H0, Hcs, init_states, final_states)

setups = [make_setup(c_dim, q_dim), make_setup(c_dim+1, q_dim)]
init_ctrls = 1e-3 * np.ones((4, pulse_len))

result = run_grape(init_ctrls, setups, dt=1)

import matplotlib.pyplot as plt
plt.plot(result.ts, result.controls[0], label='x')
plt.plot(result.ts, result.controls[1], label='y')
plt.legend()
plt.show()
