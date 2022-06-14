from pygrape import run_grape
from pygrape.setups import StateTransferSetup
from pygrape.penalties import make_amp_cost
from pygrape.preparations import make_hmt, make_target, random_waves, make_ops, unitary_to_states
from pygrape.reporters import *
import numpy as np
np.set_printoptions(precision=3, linewidth=120)
import qutip
import sys

# Operations:
# x, y, z, x2, y2: pure cavity operations, only with transmon in |g>
# mx, my, mz: coherent measurement of cavity x, y or z, i.e. map onto transmon
# mnx, mny, mnz: coherent measurement of cavity not(x), not(y) or not(z), i.e. map onto transmon
# imz: incoherent mapping of z bit value onto transmon
# imnz: incoherent mapping of not(z) onto transmon
#
# Pulselen is the number of 2 ns controls. A low-pass filter is applied and
# the optimization is done with 1 ns time steps.

PZ = qutip.ket2dm(qutip.basis(2,1))
PX = 0.5 * qutip.ket2dm(qutip.basis(2,0)+qutip.basis(2,1))
PY = 0.5 * qutip.ket2dm(qutip.basis(2,0)+1j*qutip.basis(2,1))

if len(sys.argv) > 1:
    PLEN = int(sys.argv[1])
    OPNAME = sys.argv[2]
    BIT_N = int(sys.argv[3])
    N_BITS = int(sys.argv[4])
else:
    PLEN = 400
    OPNAME = 'qft'
    BIT_N = 1
    N_BITS = 3

USE_LOSS = True
NC = 20
T1cav = 2e7
NQ = 2
T1q = 70e3
T2eq = 22e3
CHI = -2.95e-3
CHI_PRIME = 1e-6
KERR = -5.4e-6
ANHARM = -215e-3
DRIVE = 1e-3
FILT_FUNC = lambda fs: np.exp(-fs**2/(2*0.300**2))
outdir = 'output/%s_%s%s_%s' % (OPNAME, BIT_N, N_BITS, PLEN)
MAXITER = 120 * 2**N_BITS
MAXAMP = 16

def make_setup(nc, nq):
    H0, Hcs = make_hmt(nc, nq, CHI, CHI_PRIME, KERR, ANHARM, DRIVE, DRIVE)

    if OPNAME[0] == 'i':
        coherent = False
        opname = OPNAME[1:]
    else:
        coherent = True
        opname = OPNAME

    # Incoherent msmt, don't need cavity drive
    if not coherent:
        Hcs = Hcs[:2,:,:]
    n = 2**N_BITS

    # Measurements: project qubit on axis and flip transmon conditional on result
    if opname[0] == 'm':
        if opname[1] == 'n':
            invert = True
            op = opname[2]
        else:
            invert = False
            op = opname[1]

        ops = [qutip.identity(2) for _ in range(N_BITS+1)]
        flip_trans = [qutip.identity(2) for _ in range(N_BITS+1)]
        identity = qutip.tensor(flip_trans)
        if op == 'z':
            ops[BIT_N-1] = PZ
        elif op == 'x':
            ops[BIT_N-1] = PX
        elif op == 'y':
            ops[BIT_N-1] = PY

        ops.reverse()
        proj_op = qutip.tensor(ops)         # Projection operator for +<axis>

        flip_trans[-1] = qutip.sigmax()     # Flip transmon operation
        flip_trans.reverse()
        flip_trans = qutip.tensor(flip_trans)

        # operation = flip * <project+> + identity * <project->
        if not invert:
            final_op = flip_trans * proj_op + (identity - proj_op)
        else:
            final_op = proj_op + flip_trans * (identity - proj_op)

        inits = np.concatenate([
            np.array([qutip.tensor(qutip.basis(nq, 0), qutip.basis(nc, i)).full()[:,0] for i in range(n)]),
            np.array([qutip.tensor(qutip.basis(nq, 1), qutip.basis(nc, i)).full()[:,0] for i in range(n)]),
        ])

        U = np.identity(nc*nq, dtype=np.complex)
        U[:n,:n] = final_op[:n,:n]
        U[nc:nc+n,nc:nc+n] = final_op[n:,n:]
        U[:n,nc:nc+n] = final_op[:n,n:]
        U[nc:nc+n,:n] = final_op[n:,:n]
        finals = []
        for i in range(inits.shape[0]):
            finals.append(np.dot(U,inits[i,:]))
        finals = np.array(finals)

    # Register operations
    else:
        ops = [qutip.identity(2) for _ in range(N_BITS)]
        if opname == 'x':
            ops[BIT_N-1] = qutip.sigmax()
        elif opname == 'x2':
            ops[BIT_N-1] = (1j*np.pi/4*qutip.sigmax()).expm()
        elif opname == 'y2':
            ops[BIT_N-1] = (1j*np.pi/4*qutip.sigmay()).expm()
        elif opname == 'z':
            ops[BIT_N-1] = qutip.sigmaz()
        elif opname == 'qft':
            xs = np.arange(n) / float(n)
            ops = [qutip.Qobj(np.array(
                [1/np.sqrt(n)*np.exp(1j*2*np.pi*i*xs) for i in range(n)]))]
        ops.reverse()
        op = qutip.tensor(ops).full()

        inits = np.array([qutip.tensor(qutip.basis(nq, 0), qutip.basis(nc, i)).full()[:,0] for i in range(n)])
        finals = np.zeros((n,nq*nc), dtype=np.complex)
        finals[:n,:n] = op

    a, ad, b, bd = make_ops(nc, nq)
    if USE_LOSS:
        loss_vec = np.ones(nc*nq) - ((a.dag()*a) * 0.5/T1cav + (b.dag()*b) * 0.5/T1q).diag()
    else:
        loss_vec = None

    return StateTransferSetup(H0, Hcs, inits, finals, coherent=coherent, loss_vec=loss_vec)

def make_gauge(nc, nq):
    a, ad, b, bd = make_ops(nc, nq)
    return [(ad*a).full()]

if OPNAME[0] == 'i':
    setups = [make_setup(NC, NQ)]
else:
    setups = [make_setup(NC, NQ), make_setup(NC+1, NQ)]

penalties = [make_amp_cost(1e-4, MAXAMP)]
wave_names = 'qI,qQ,cI,cQ'.split(',')

reporters = [
    print_costs(),
    save_waves(wave_names, 20),
    plot_waves(wave_names, 20),
    plot_fidelity(4),
#    update_gauges(gauge_ops, 20),
    plot_states(5),
    # verify_from_setup(make_setup(NC, NQ+1), 40),
]

if OPNAME[0] == 'i':
    init_ctrls = random_waves(2, PLEN, npoints=20)
else:
    init_ctrls = random_waves(4, PLEN, npoints=20)

ret = run_grape(init_ctrls, setups, penalties, reporters, outdir,
            iprint=0, maxcor=20, maxiter=MAXITER, n_proc=1,
            n_ss=2, dt=2, filt_func=FILT_FUNC,
            )
# If refining with smaller time step
#ret = run_grape(ret.raw_controls, setups, penalties, reporters, outdir, iprint=1, maxcor=20, maxiter=20, n_ss=4, dt=2, filt_func=FILT_FUNC)
