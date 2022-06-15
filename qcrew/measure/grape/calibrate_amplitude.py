from init_script import qA_ge, cA
import numpy as np
from pygrape import run_grape, UnitarySetup
from system_hamiltonian import make_hmt
from scipy.optimize import fmin

OPT_DISPLACEMENT = False


cavity = cA
qubit = qA_ge

if OPT_DISPLACEMENT:
    dim = 20
    amp = cavity.pulse.unit_amp
    sig = cavity.pulse.sigma
else:
    dim = 5
    amp = qubit.pulse.unit_amp
    sig = qubit.pulse.sigma

dt = 1
ts = dt * np.arange(-2*sig/dt, 2*sig/dt)
pulse = amp * np.exp(-ts**2 / (2.*sig**2))

if OPT_DISPLACEMENT:
    H0, Hcs = make_hmt(dim, 1)
else:
    H0, Hcs = make_hmt(1, dim)


def cost(params):
    rabi = params[0]
    setup = UnitarySetup(H0, [rabi*Hcs[0], rabi*Hcs[1]], np.eye(dim))
    ret = run_grape(np.array([pulse.real, pulse.imag]), setup, dt=dt, n_ss=1, reporter_fns=[],
                    response=None, shape_sigma=0, eval_once=True, impulse_data=None)
    if OPT_DISPLACEMENT:
        c = (1 - np.sum(np.arange(dim) * abs(ret.props[0][:,0])**2))**2
    else:
        c = -abs(ret.props[0][0,1])
    print '\r', abs(ret.props[0][:4,0])**2,
    return c

rabi = fmin(cost, [10e-3], ftol=1e-9)
print rabi / (2*np.pi)
