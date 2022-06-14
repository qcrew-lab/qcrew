import numpy as np
from pygrape import *

import qutip

q_dim = 3
c_dim = 8
pulse_len = 1000
dt = 2
outdir = 'make_11'

# In GHZ
anharm = -.1165
kerr_a = -2e-6
kerr_b = -2e-6
chi_bq = -1.08e-3
chi_aq = -1.04e-3
q_drive = QD = 2 * np.pi * 1e-3 * 196
c1_drive = CD_a = 2 * np.pi * 1e-3 * 279
c2_drive = CD_b = 2 * np.pi * 1e-3 * 158


def make_setup(c_dim, q_dim):
    a = qutip.tensor(qutip.destroy(c_dim),qutip.qeye(c_dim),qutip.qeye(q_dim))
    b = qutip.tensor(qutip.qeye(c_dim),qutip.destroy(c_dim),qutip.qeye(q_dim))
    q = qutip.tensor(qutip.qeye(c_dim),qutip.qeye(c_dim),qutip.destroy(q_dim))
    ad = a.dag()
    bd = b.dag()
    qd = q.dag()
    H0 = (anharm/2) * qd * qd * q * q
    H0 += (kerr_a/2) * ad * ad * a * a
    H0 += (kerr_b/2) * bd * bd * b * b
    H0 += (chi_aq) * ad * a * qd * q
    H0 += (chi_bq) * bd * b * qd * q
    H0 *= 2*np.pi
    Hcs = [QD*(q + qd), 1j*QD*(q - qd), CD_a*(a + ad), 1j*CD_a*(a - ad), CD_b*(b + bd), 1j*CD_b*(b - bd)]

    init_states = [
        qutip.tensor(qutip.basis(c_dim, 0), qutip.basis(c_dim, 0), qutip.basis(q_dim, 0))
    ]

    final_states = [
        qutip.tensor(qutip.basis(c_dim, 1), qutip.basis(c_dim, 1), qutip.basis(q_dim, 0))
    ]

    setup = StateTransferSetup(H0, Hcs, init_states, final_states, use_taylor=True, sparse=True)
    setup.taylor_order = 12
    return setup




if __name__ == '__main__':
    setups = [make_setup(c_dim, q_dim), make_setup(c_dim+1,q_dim)]
#    setups[0].optimize_taylor_order(0.02, 100, 2, init_order=10)

    init_ctrls = 5e-4 * random_waves(6, pulse_len, 20)
    
    
    reporters = [
        print_costs(),
        save_waves(['qI','qQ','aI','aQ', 'bI', 'bQ'], 5),
        plot_waves(['qI','qQ','aI','aQ', 'bI', 'bQ'], 5),
        plot_trajectories(setups[0], 10),
        plot_states(10),
        plot_fidelity(10),
        verify_from_setup(make_setup(c_dim+2, q_dim), 10),
    ]
    
    penalties = [
        make_amp_cost(1e-4, 0.02),
        make_lin_deriv_cost(1e-2)
    ]
    
    result = run_grape(init_ctrls, setups, outdir=outdir,
                       penalty_fns=penalties, reporter_fns=reporters, 
                       dt=dt, discrepancy_penalty=1e6, 
                       n_proc=2, save_data=10)
    
    
    import matplotlib.pyplot as plt
    plt.subplot(311)
    plt.plot(result.ts, result.controls[0], label='x')
    plt.plot(result.ts, result.controls[1], label='y')
    plt.subplot(312)
    plt.plot(result.ts, result.controls[2], label='x')
    plt.plot(result.ts, result.controls[3], label='y')
    plt.subplot(313)
    plt.plot(result.ts, result.controls[4], label='x')
    plt.plot(result.ts, result.controls[5], label='y')
    plt.legend()
    plt.show()