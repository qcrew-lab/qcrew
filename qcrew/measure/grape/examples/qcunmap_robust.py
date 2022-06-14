from pygrape import *

PLEN = 600
DT = 1
NC = 20
NQ = 3
CHI = -1.9685e-3
CHI_PRIME = 1.3e-6
KERR = -4.6e-6
ANHARM = -297.06e-3
Q_DRIVE = C_DRIVE = 1e-3
T1_CAV = 235e3
DEFLATE_TIME = 1 / (4 * KERR)
ALPHA = np.sqrt(3) * np.exp(-DEFLATE_TIME / (2*T1_CAV))
D_PHASE = 8 * np.pi / 180
N_PHASES = 10
SIGN = 1

def make_states(nc, nq, sign=SIGN):
    def cat(a, s):
        x = (qutip.coherent(nc, a) + s*qutip.coherent(nc, -a))
        x /= x.norm()
        return x
    phases = np.linspace(-D_PHASE / 2, D_PHASE/2, N_PHASES)

    inits, finals = [], []
    for phase in phases:
        pf = np.exp(-1j*phase)
        cat_h = cat(pf*ALPHA, sign)
        cat_v = cat(-1j*pf*ALPHA, sign)
        gnd = qutip.basis(nq, 0)
        exc = qutip.basis(nq, 1)

        inits.extend([
            qutip.tensor(gnd, cat_h),
            qutip.tensor(gnd, cat_v),
        ])
        finals.extend([
            qutip.tensor(gnd, cat_h),
            qutip.tensor(exc, cat_h),
        ])

    return inits, finals

def make_setup(nf, nq):
    H0, Hcs = make_hmt(nf, nq, CHI, CHI_PRIME, KERR, ANHARM, Q_DRIVE, C_DRIVE)
    inits, finals = make_states(nf, nq)
    gauge_ops = []
    for i in range(NC):
        op = np.zeros((nf, nf), complex)
        op[i, i] = 1
        gauge_ops.append(np.kron(np.eye(nq), op))
    for i in range(NC):
        for j in range(i+1, NC):
            op = np.zeros((nf, nf), complex)
            op[i, j] = 1
            op[j, i] = 1
            gauge_ops.append(np.kron(np.eye(nq), op))
            op = np.zeros((nf, nf), complex)
            op[i, j] = +1j
            op[j, i] = -1j
            gauge_ops.append(np.kron(np.eye(nq), op))
    return StateTransferSetup(H0, Hcs, inits, finals, gauge_ops)

def expect_setup(nf, nq):
    a, ad, b, bd = make_ops(nf, nq)
    e_op = -0.02 * ad * a
    H0, Hcs = make_hmt(nf, nq, CHI, CHI_PRIME, KERR, ANHARM, Q_DRIVE, C_DRIVE)
    inits, finals = make_states(nf, nq)
    return ExpectationSetup(H0, Hcs, inits[0], e_op)

def run_with_dt(init_controls, init_gauges, dt):
    setups = [make_setup(NC, NQ), make_setup(NC+1, NQ), expect_setup(NC, NQ)]
    outdir = 'output/qcunmap_robust_' + {1: 'even', -1: 'odd'}[SIGN]


    wave_names = 'qI,qQ,cI,cQ'.split(',')
    reporters = [
        print_costs(),
        print_grads(),
        save_script(__file__),
        save_waves(wave_names, 25),
        plot_waves(wave_names, 25),
        plot_fidelity(25),
        # plot_cwigs(NC, 50, indices=[0,1,8,9]),
        verify_from_setup(make_setup(NC, NQ+1), 25),
    ]
    penalties = [
        make_deriv_cost(1e-5, .5)
    ]

    ret = run_grape(
        init_controls, setups, dt=dt, n_proc=3, outdir=outdir,
        penalty_fns=penalties, reporter_fns=reporters, init_aux_params=init_gauges,
    )
    print ret.message
    return ret

init_controls = random_waves(4, PLEN, npoints=5)
init_gauges = np.zeros((NC**2))
ret = run_with_dt(init_controls, init_gauges, 1)
# ss_controls = np.zeros((4, 2*PLEN))
# ss_controls[:, 0::2] = ret.raw_controls
# ss_controls[:, 1::2] = 0.5*(ret.raw_controls + np.roll(ret.raw_controls, 1, axis=1))
# ret = run_with_dt(ss_controls, ret.aux_params, 1)
