import numpy as np
from pygrape import *

import qutip

q_dim = 3
c_dim = 8
pulse_len = 1200
dt = 2
outdir = "20220614_test"

# In GHZ
### A params
if 1:
    anharm = -0.195
    kerr_b = 0
    chi_bq = -3.2e-4

    q_drive = QD = 2 * np.pi * 0.1
    c2_drive = CD = 2 * np.pi * 0.1


def make_setup(c_dim, q_dim):
    s = qutip.tensor(qutip.destroy(c_dim), qutip.qeye(q_dim))
    q = qutip.tensor(qutip.qeye(c_dim), qutip.destroy(q_dim))
    sd = s.dag()
    qd = q.dag()
    H0 = (anharm / 2) * qd * qd * q * q
    H0 += (kerr_b / 2) * sd * sd * s * s
    H0 += (chi_bq) * sd * s * qd * q
    H0 *= 2 * np.pi

    Hcs = [QD * (q + qd), 1j * QD * (q - qd), CD * (s + sd), 1j * CD * (s - sd)]

    init_states = [qutip.tensor(qutip.basis(c_dim, 0), qutip.basis(q_dim, 0))]

    final_states = [qutip.tensor(qutip.basis(c_dim, 0), qutip.basis(q_dim, 1))]

    setup = StateTransferSetup(
        H0, Hcs, init_states, final_states, use_taylor=True, sparse=True
    )
    setup.taylor_order = 16
    return setup


if __name__ == "__main__":
    setups = [make_setup(c_dim, q_dim), make_setup(c_dim + 1, q_dim)]

    init_ctrls = 5e-4 * random_waves(4, pulse_len, 20)

    reporters = [
        print_costs(),
        save_waves(["qI", "qQ", "cav_I", "cav_Q"], 5),
        plot_waves(["qI", "qQ", "cav_I", "cav_Q"], 5),
        # plot_trajectories(setups[0], 10),
        # plot_states(10),
        # plot_fidelity(10),
        verify_from_setup(make_setup(c_dim + 2, q_dim), 10),
    ]

    penalties = [make_amp_cost(1e-4, 0.02), make_lin_deriv_cost(1e-2)]

    result = run_grape(
        init_ctrls,
        setups,
        outdir=outdir,
        penalty_fns=penalties,
        reporter_fns=reporters,
        dt=dt,
        discrepancy_penalty=1e6,
        n_proc=2,
        save_data=10,
    )

    import matplotlib.pyplot as plt

    plt.subplot(211)
    plt.plot(result.ts, result.controls[0], label="x")
    plt.plot(result.ts, result.controls[1], label="y")
    plt.subplot(212)
    plt.plot(result.ts, result.controls[2], label="x")
    plt.plot(result.ts, result.controls[3], label="y")
    #    plt.subplot(313)
    #    plt.plot(result.ts, result.controls[4], label='x')
    #    plt.plot(result.ts, result.controls[5], label='y')
    plt.legend()
    plt.show()
