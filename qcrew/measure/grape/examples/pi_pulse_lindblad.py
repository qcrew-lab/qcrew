import numpy as np
from pygrape import *

H = np.array([
    [0, 0],
    [0, 1],
])
Hc = np.array([
    [0, 1],
    [1, 0],
])
U_target = np.array([
    [0, 1],
    [1, 0],
])
c_ops = [np.array([
    [0, .1],
    [0,  0],
])]
setup = LindbladSetup(H, [Hc], c_ops, U_target, np.eye(2))
init_ctrls = 1e-3 * np.ones((1, 200))

reporters = [
    print_costs(),
    # Non-hermitian value should be strictly less than lindblad value
    verify_from_setup(UnitarySetup(H, [Hc], U_target, c_ops=c_ops), 10),
    # Value from qutip.mesolve should match fidelity approximately
    verify_master_equation(StateTransferSetup(H, [Hc], U_target, np.eye(2)), c_ops, 10)
]

result = run_grape(init_ctrls, [setup], reporter_fns=reporters, dt=.2, ftol=1e-8)


import matplotlib.pyplot as plt
plt.plot(result.ts, result.controls[0])
#plt.savefig('../docs/_static/pi_pulse_lindblad_ctrls.png')
plt.show()
