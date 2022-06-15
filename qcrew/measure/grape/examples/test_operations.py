from operations import *
from pygrape import *

def test(idx):
    op = [
        FlipParityOp(0),
        FlipParityOp(2),
        SwapPhotonStatesOp(1),
        SwapPhotonStatesOp(3),
        SwapPhotonStatesOp(7),
        QcmapOp(),
        MeasureParity(0),
        MeasureParity(2),
    ][idx]
    op.add_chi(3e-3, 0, 1)
    op.add_anharm(5e-6, 0)
    op.add_iq_drives(1e-3, 0)
    op.add_iq_drives(1e-3, 1)
    op.add_t1(1e6, 0)
    op.add_t1(80e3, 1)
    op.add_t2(30e3, 1)
    setup = op.make_setup(taylor=True, lindblad=False)
    setup.optimize_taylor_order(10, 400, 2)
    taylor_order = setup.taylor_order
    penalties = [
        # make_l1_wvd_penalty_cuda(5e-10, 600)
        make_lin_deriv_cost(1e-5),
        # make_amp_cost(1e-4, 15),
    ]
    init_ctrls = random_waves(4, 350)
    # init_ctrls = 3*np.random.randn(4, 600)
    reporters = [
        print_costs(),
        # print_grads(),
        liveplot_waves(op.wave_names),
        liveplot_prop(5),
    ]
    ret = run_grape(init_ctrls, setup, penalties, reporters, outdir=op.name, basinhop=False, dt=2, test_cost=0)
    init_ctrls = ret.raw_controls
    setup = op.make_setup(taylor=True, lindblad=True)
    setup.taylor_order = taylor_order
    ret = run_grape(init_ctrls, setup, penalties, reporters, outdir=op.name, basinhop=False, dt=2, test_cost=0)



if __name__ == '__main__':
    test(0)
    # pool = Pool(4)
    # pool.map(4)



