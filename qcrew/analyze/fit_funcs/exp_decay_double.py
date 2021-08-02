import numpy as np

def func(xs, A=1, B=1, tau=1, tau1=1, ofs=0):
    return A * np.exp(-xs / tau) + B * np.exp(-xs / tau1) + ofs

def guess(xs, ys):
    yofs = ys[-1]
    ys_ofs = ys - yofs
    span = xs[-1] - xs[0]
    return dict(
        A 		= ys_ofs[0]/2,
        B 		= ys_ofs[0]/2,
        tau 	= span / 3,
        tau1	= span / 15,
        ofs 	= yofs,
    )
