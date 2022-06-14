from pygrape import *

NQ = 2
NC = 20
chi = 3e-3
drive = 1e-3
plen = int(1 / (2 * chi)) + 25

def make_setup(NC):
    a = qutip.tensor(qutip.qeye(NQ), qutip.destroy(NC))
    ad = a.dag()
    b = qutip.tensor(qutip.destroy(NQ), qutip.qeye(NC))
    bd = b.dag()



    H0 = 2 * np.pi * chi * ad*a*bd*b
    Hx = 2 * np.pi * drive * (b + bd)
    Hy = 2j* np.pi * drive * (b - bd)

    inits, finals = [], []
    for i in range(8):
        inits.append(qutip.ket([0, i], [NQ, NC]))
        finals.append(qutip.ket([i%2, i], [NQ, NC]))

    loss_vec = 1 - np.eye(NC)[-1]
    # loss_vec = np.ones(NC)
    loss_vec = np.kron(np.ones(2), loss_vec)
    return StateTransferSetup(H0, [Hx, Hy], inits, finals, coherent=False, loss_vec=loss_vec)

setup = make_setup(NC)
init_ctrls = 10*random_waves(2, plen, 10)


penalties = [
    make_lin_deriv_cost(5e-5),
    make_l1_penalty(1e-4, 1e2)
]
reporters = [
    print_costs(),
    liveplot_waves(['qI', 'qQ'], 5),
    verify_from_setup(make_setup(NC+1), 5),
]

run_grape(init_ctrls, setup, penalty_fns=penalties, reporter_fns=reporters)
