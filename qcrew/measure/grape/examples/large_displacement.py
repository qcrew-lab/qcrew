from grape import run_grape
from preparations import random_waves, random_pulse
from reporters import print_costs, liveplot_waves, plot_waves, save_waves
from penalties import make_deriv_cost, make_amp_cost
from qutip import destroy, coherent
from math import pi, sqrt
import numpy as np

base_n_cav = 75
kerr = 13e-6
drive = 1e-3
chi = 600e-6
final_nbar = 50
pulse_len = 250
dt = 4
sparse = True


def make_setup(n_cav, detune, final_nbar, scale):
    a = destroy(n_cav)
    ad = a.dag()
    H0 = 2 * pi * (detune * ad * a + (kerr/2) * ad * ad * a * a)
    Hc_x = 2  * pi * drive * (a + ad)
    Hc_y = 2j * pi * drive * (a - ad)
    init = coherent(n_cav, 0)
    H0 = H0.full()
    Hc_x = Hc_x.full()
    Hc_y = Hc_y.full()
    init = init.full().T
    # Create diagonal operator M that is maximized for n = final_nbar
    # M = -n^2 + b*n
    # dM/dn(nf) = -2*nf + b == 0
    # b = (2*nf)
    n_op = ad * a
    expect_op = scale*(-n_op*n_op + 2*final_nbar*n_op)

    return H0, [Hc_x, Hc_y], init[0], expect_op.full()


init_controls = np.array([
    0.5*np.ones(pulse_len),
    0.0*np.ones(pulse_len),
])

setups = [
    #          Dimension     Detuning  Target N    Weight
    make_setup(base_n_cav,   0,        final_nbar, 1e-2),
    make_setup(base_n_cav+1, 0,        final_nbar, 1e-2),
    make_setup(base_n_cav,   chi,      0,          1),
    make_setup(base_n_cav,   chi*1.25, 0,          1),
    make_setup(base_n_cav,   chi*1.5,  0,          1),
    make_setup(base_n_cav,   chi*2,    0,          1),
]

penalties = [make_amp_cost(1e-4, 50)]
wave_names = ['cI', 'cQ']
reporters = [
    print_costs(),
    #liveplot_waves(wave_names),
    plot_waves(wave_names, 10),
    save_waves(wave_names, 10)
]
outdir = 'output/displacement'

data, ret = run_grape(init_controls, setups, penalties, reporters, outdir, dt)
print ret.message