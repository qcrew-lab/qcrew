import qutip as q
import numpy as np
import scipy.sparse.linalg
from pygrape.cugrape.configure_cugrape import configure, get_hmt_ops
from pygrape.cugrape.almohy import get_taylor_params
from pygrape.setups import StateTransferSetup
from pygrape.cuda_setup import CudaStateTransferSetup

def get_Hs(mode_dims, dt, numeric=False):
    def destroy(n):
        ops = [q.qeye(d) for d in mode_dims]
        ops[n] = q.destroy(mode_dims[n])
        return q.tensor(*list(reversed(ops)))

    n_modes = len(mode_dims)
    if numeric:
        ops = map(destroy, range(n_modes))
        ops = [(a, a.dag()) for a in ops]
    else:
        ops = get_hmt_ops(n_modes)

    kerr = dt*1e-5
    chi = dt*1e-3
    drive = dt*1e-2
    H0 = 0
    Hcs = []
    for i, (d, (a, ad)) in enumerate(zip(mode_dims, ops)):
        if d > 2:
            H0 += d*kerr/2 * (ad*ad*a*a)
        for b, bd in ops[i+1:]:
            H0 += d*chi * ad*a*bd*b
        Hcs.append(drive*(a + ad))
        Hcs.append(1j*drive*(a - ad))
    if numeric:
        H0 = H0.data.tocsr()
        Hcs = [H.data.tocsr() for H in Hcs]
    return H0, Hcs



class TimeSuite:
    params = [
        # mode_dims
        [[[2, 20, 20], [2, 19, 20]], [[2, 2, 2, 2, 20], [2, 2, 2, 2, 19]]],
        # plen
        [50, 250, 2000],
        # dt
        [0.1, 1],
        # nstate
        [8, 1],
        # double
        [False],
        # n_step
        [10],
        # use_gpu
        [False, True],
    ]

    def setup(self, mode_dims, plen, dt, nstate, double, n_step, use_gpu):
        print('Params:', mode_dims, plen, dt, nstate, double, n_step, use_gpu)
        H0, Hcs = get_Hs(mode_dims[0], dt, numeric=True)
        Hnorm = scipy.sparse.linalg.norm(H0 + sum(Hcs), 1)
        taylor_order, n_rep = get_taylor_params(Hnorm, 1e-8)
        assert n_rep == 1, (Hnorm, taylor_order, n_rep)

        nctrls = len(Hcs)
        np.random.seed(12345)
        psi0s, psifs = [], []
        for mds in mode_dims:
            dim = np.product(mds)
            psi0 = np.random.randn(nstate, dim) + 1j*np.random.randn(nstate, dim)
            psi0 /= np.linalg.norm(psi0, axis=1)[:,None]
            psi0s.append(psi0)
            psif = np.random.randn(nstate, dim) + 1j*np.random.randn(nstate, dim)
            psif /= np.linalg.norm(psif, axis=1)[:,None]
            psifs.append(psif)
        controls = np.random.randn(nctrls, plen)
        self.all_controls = np.random.randn(n_step, nctrls, plen)

        self.grape_setups = []
        if use_gpu:
            H0, Hcs = get_Hs(mode_dims[0], dt, numeric=False)
            setup = CudaStateTransferSetup(mode_dims, H0, Hcs, psi0s, psifs, taylor_order, double)
            setup.init_cugrape(plen, 1)
            self.grape_setups.append(setup)
        else:
            for mds, psi0, psif in zip(mode_dims, psi0s, psifs):
                H0, Hcs = get_Hs(mds, dt, numeric=True)
                setup = StateTransferSetup(H0, Hcs, psi0, psif, sparse=True, use_taylor=True)
                setup.set_dtype(np.complex128 if double else np.complex64)
                self.grape_setups.append(setup)

    def time_run_steps(self, *args):
        for ctrls in self.all_controls:
            for setup in self.grape_setups:
                setup.get_fids(ctrls, [], 1)

# if __name__ == '__main__':
#     ts = TimeSuite()
#     ts.setup(*(list(zip(*ts.params))[0]))
#     ts.time_run_steps(*(list(zip(*ts.params))[0]))
