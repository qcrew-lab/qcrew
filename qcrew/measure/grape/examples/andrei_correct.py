from pygrape import *
import os
import sys

if len(sys.argv) > 1:
    NAME = sys.argv[0]
    PLEN = int(sys.argv[2])
else:
    NAME = 'pump'
    PLEN = 400
NC = 20
NQ = 2
CHI = -1.9685e-3
CHI_PRIME = 1.3e-6
KERR = -4.7e-6
ANHARM = -297.06e-3
# Q_DRIVE = 2.3729032170376996e-06
# C_DRIVE = 1.5229080348152402e-06
Q_DRIVE = C_DRIVE = 1e-3
T1 = 50e3
T2 = 14e3
TCAV = 250e3
INIT_AMP = 1000
MAX_AMP = 25000
DT = -1 / (4*KERR)
ALPHA = np.sqrt(3)
ALPHA_2 = np.sqrt(2)
LOAD_ITER = None
GAUGE_SPACING = 15
F_STATE_PASS = False
FILT_FUNC = lambda f: 1 / np.sqrt(1 + (f / .10)**2)


def make_states(nc, nq):
    return {
        'correct': make_states_correct,
        'qcunmap': make_states_qcunmap,
        'qcunmap_minus': make_states_qcunmap_minus,
        'qcmap': make_states_qcmap,
        'pump': make_states_pump,
    }[NAME](nc, nq)


def make_states_qcmap(nc, nq):
    def cat(a, s):
        x = (qutip.coherent(nc, a) + s*qutip.coherent(nc, -a))
        x /= x.norm()
        return x
    vacuum = qutip.basis(nc, 0)
    cat_p_1 = cat(ALPHA, 1)
    cat_ip_1 = cat(1j*ALPHA, 1)
    gnd = qutip.basis(nq, 0)
    exc = qutip.basis(nq, 1)

    inits = [
        qutip.tensor(gnd, vacuum),
        qutip.tensor(exc, vacuum),
    ]
    finals = [
        qutip.tensor(gnd, cat_p_1),
        qutip.tensor(gnd, cat_ip_1),
    ]
    return inits, finals


def make_states_qcunmap_minus(nc, nq):
    return make_states_qcunmap(nc, nq, sign=-1)


def make_states_qcunmap(nc, nq, sign=1):
    def cat(a, s):
        x = (qutip.coherent(nc, a) + s*qutip.coherent(nc, -a))
        x /= x.norm()
        return x
    vacuum = qutip.basis(nc, 0)
    alpha_2 = ALPHA * np.exp(-DT / (2*TCAV))
    cat_h = cat(alpha_2, sign)
    cat_v = cat(1j*alpha_2, sign)
    gnd = qutip.basis(nq, 0)
    exc = qutip.basis(nq, 1)

    inits = [
        qutip.tensor(gnd, cat_h),
        qutip.tensor(gnd, cat_v),
    ]
    finals = [
        qutip.tensor(gnd, vacuum),
        qutip.tensor(exc, vacuum),
    ]

    return inits, finals

def make_states_pump(nc, nq, sign=1):
    def cat(a, s):
        x = (qutip.coherent(nc, a) + s*qutip.coherent(nc, -a))
        x /= x.norm()
        return x
    cat_h_1 = cat(ALPHA, sign)
    cat_v_1 = cat(1j*ALPHA, sign)
    cat_h_2 = cat(ALPHA_2, sign)
    cat_v_2 = cat(1j*ALPHA_2, sign)
    gnd = qutip.basis(nq, 0)

    inits = [
        qutip.tensor(gnd, cat_h_2),
        qutip.tensor(gnd, cat_v_2),
    ]
    finals = [
        qutip.tensor(gnd, cat_h_1),
        qutip.tensor(gnd, cat_v_1),
    ]
    print 'init overlap', abs((inits[0].dag() * inits[1])[0, 0])
    print 'final overlap', abs((finals[0].dag() * finals[1])[0, 0])
    print 'init-final ovlps', [abs((i.dag() * f)[0, 0]) for i, f in zip(inits, finals)]

    return inits, finals

def make_states_correct(nf, nq):
    def cat(a, s):
        x = (qutip.coherent(nf, a) + s*qutip.coherent(nf, -a))
        x /= x.norm()
        return x

    cat_p_1 = cat(ALPHA, 1)
    cat_ip_1 = cat(1j*ALPHA, 1)
    gnd = qutip.basis(nq, 0)
    exc = qutip.basis(nq, 1)

    a = qutip.destroy(nf)
    ad = a.dag()
    kerr_H = 0 * (2 * pi * KERR / 2) * (ad * ad * a * a)

    ts = np.linspace(0, DT, 100)
    c_ops = [np.sqrt(1 / TCAV) * a]
    inits, finals = [], []

    for angle, state in ((1, cat_p_1), (1j, cat_ip_1)):
        result = qutip.mesolve(kerr_H, state, ts, c_ops, [])
        rho = result.states[-1]
        vals, vecs = rho.eigenstates()
        phase_1 = np.exp(-1j*np.angle(vecs[-1][0]))[0,0]
        phase_2 = np.exp(-1j*np.angle(vecs[-2][1]))[0,0]
        no_error_state = vecs[-1] * phase_1
        error_state = vecs[-2] * phase_2
        alpha_2_1 = np.sqrt(qutip.expect(ad * a, no_error_state))
        # final_state = cat(angle*alpha_2_1, 1)
        final_state = state
        inits.append(qutip.tensor(gnd, no_error_state))
        finals.append(qutip.tensor(gnd, final_state))
        inits.append(qutip.tensor(gnd, error_state))
        finals.append(qutip.tensor(exc, final_state))

    return inits, finals


def make_target(nf, nq):
    inits, finals = make_states(nf, 2)
    Usub = sum(f * i.dag() for i, f in zip(inits, finals)).data.todense()
    U = np.zeros((nf*nq, nf*nq), dtype=np.complex)
    U[:2*nf, :2*nf] = Usub
    return U


def make_setup(nf, nq, drive_fac=1):
    H0, Hcs = make_hmt(nf, nq, CHI, CHI_PRIME, KERR, ANHARM, drive_fac*Q_DRIVE, drive_fac*C_DRIVE)
    inits, finals = make_states(nf, 2)
    inits = np.array([s.full()[:, 0] for s in inits])
    finals = np.array([s.full()[:, 0] for s in finals])
    return StateTransferSetup(H0, Hcs, inits, finals)

def make_gauge(nc, nq):
    a, ad, b, bd = make_ops(nc, nq)
    return [(ad*a).full(), (bd * b).full()]

setups = [make_setup(NC, NQ), make_setup(NC+1, NQ)]
penalties = [make_amp_cost(1e-4, 80), make_deriv_cost(5e-5, 3)]
wave_names = 'qI,qQ,cI,cQ'.split(',')
outdir = 'output/%s_%s' % (NAME, PLEN)
if LOAD_ITER is None:
    init_ctrls = random_waves(4, PLEN, 6)
else:
    data = np.load(os.path.join(outdir, str(LOAD_ITER), 'waves.npz'))
    init_ctrls = np.array([data['raw_' + k] for k in wave_names])
states = make_states(NC, NQ)
c_ops = make_c_ops(NC, NQ, T1, T2, TCAV)
gauge_ops = [make_gauge(NC, NQ), make_gauge(NC+1, NQ)]
reporters = [
    print_costs(),
    # verify_master_equation(states, c_ops, 60),
    save_waves(wave_names, 20),
    plot_waves(wave_names, 20),
    # liveplot_waves(wave_names, 1),
    plot_fidelity(20),
    # plot_cwigs(states, 100),
    # verify_from_setup(make_setup(NC, NQ+1), 40),
    # update_gauges(gauge_ops, GAUGE_SPACING),
]

print 'NAME:', NAME
print 'PLEN:', PLEN
print 'NC:', NC
print 'NQ:', NQ
print 'ALPHA:', ALPHA
print 'DT:', DT

data = run_grape(init_ctrls, setups, penalties, reporters, outdir,
                 n_proc=len(setups), gtol=1e-7, maxcor=100, dt=2)
print data.message

if F_STATE_PASS:
    NQ += 1
    setups = [make_setup(NC, NQ), make_setup(NC+1, NQ)]
    states = make_states(NC, NQ)
    c_ops = make_c_ops(NC, NQ, T1, T2, TCAV)
    gauge_ops = [make_gauge(NC, NQ), make_gauge(NC+1, NQ)]
    init_ctrls = data['raw_controls']
    reporters = [
        print_costs(),
        # verify_master_equation(states, c_ops, 60),
        save_waves(wave_names, 20),
        plot_waves(wave_names, 20),
        plot_fidelity(20),
        # plot_cwigs(states, 100),
        # verify_from_setup(make_setup(NC, NQ+1), 40),
        # update_gauges(gauge_ops, GAUGE_SPACING),
    ]
    run_grape(init_ctrls, setups, penalties, reporters, outdir,
              maxcor=100, dt=2, n_ss=2, filt_func=FILT_FUNC)
