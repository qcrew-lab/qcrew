from operations import CavityQubitOp
from pygrape import run_grape, random_waves, print_costs, plot_states


op = CavityQubitOp(15, 2)

op.add_chi(2e-3, 0, 1)
op.add_iq_drives(1e-3, 0)
op.add_iq_drives(1e-3, 1)
op.inits = [op.basis(0, 0)]
op.finals = [op.basis(1, 0), op.basis(2, 0)]

setup = op.make_setup(subspace=True)
reporters = [print_costs(), plot_states()]

init_controls = .05 * random_waves(4, 500)
ret = run_grape(init_controls, setup, reporter_fns=reporters, check_grad=5, gtol=1e-8)
print ret.message
