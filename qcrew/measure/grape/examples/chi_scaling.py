from scipy.linalg import expm
import numpy as np
import matplotlib.pyplot as plt

from operations import CavityQubitOp, run_operation
from pygrape import random_hermitian

DIM = 2
PLENS = (300,)
NC = 10
N_OP = 5
MAXITER = 200
FTOL = 1e-6
CHI_RANGE = 1e-3, 1e-2, 10


class CavityUnitaryOp(CavityQubitOp):
    def __init__(self, U, **kwargs):
        super(CavityUnitaryOp, self).__init__(**kwargs)
        n = len(U)
        self.inits = [self.g_state(k) for k in range(n)]
        self.finals = [sum(U[i, j] * self.inits[j] for j in range(n)) for i in range(n)]


def find_speed_limit(U, init_plen, resolution=10, **kwargs):
    lb, ub = 0, 2*init_plen
    plen = init_plen
    while True:
        kws = dict(
            term_fid=.99, report_interval=200, check_grad=None,
            discrepancy_penalty=1e4, solver_opts=dict(maxiter=MAXITER, ftol=FTOL),
            print_costs=False, save_data=False, dt=2, impulse_fname=None,
            amp_penalty=0, deriv_penalty=0
        )
        kws.update(kwargs)
        ret = run_operation(CavityUnitaryOp, plen, op_kwargs=dict(U=U), **kws)
        f = ret.fids.mean()
        if f >= .99:
            ub = plen
        else:
            lb = plen
        print '%d %.2f --> (%d, %d) [%s]' % (plen, f, lb, ub, ret.message)
        if (ub - lb) < resolution:
            break
        plen = int(.5*(ub + lb))
    return (lb, ub)


if __name__ == '__main__':
    for _ in range(N_OP):
        H = random_hermitian(DIM)
        U = expm(-1j*H)

        bounds = []
        chis = np.linspace(*CHI_RANGE)
        for chi in chis:
            l1, u1 = find_speed_limit(U, 256, resolution=4, c_levels=10, chi=chi)
            bounds.append(2*.5*(l1 + u1))
            print '='*25
            print 'Chi: %.3g Bound %d' % (chi, bounds[-1])
            print '='*25

        plt.figure()
        plt.plot(chis, bounds)
        plt.xlabel('Chi (MHz)')
        plt.ylabel('Minimum Time (ns)')
        plt.savefig('chi_scaling.pdf')
