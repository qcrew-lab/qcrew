import numpy as np
import math

def func(xs, dispscale=1.0, amp=1, ofs=0, n=0):
    alphas = xs * dispscale
    nbars = alphas**2
    return ofs + amp * nbars**0 / math.factorial(0) * np.exp(-nbars)

def guess(xs, ys):
    mul = -1 if (xs[-1] > xs[0]) else 1
    amp = mul*(ys[-1]-ys[0])
    ofs = np.max(ys) if (amp < 0) else np.min(ys)
    return dict(
        dispscale=1.0, n=0,
        amp=amp, ofs=ofs,
    )