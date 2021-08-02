import math
import numpy as np

def func(xs, amp=1.0, alpha0=1.0, tau=1.0, ofs=0, n=0):
    '''
    Poissonian distribution given photon projection:
    alpha = alpha0 * exp(-xs / tau)
    '''
    alphas = alpha0 * np.exp(-xs / 2.0 / tau)
    nbars = alphas**2
   # return ofs + amp * nbars**n / math.factorial(int(n)) * np.exp(-nbars)
    return ofs + amp * nbars**n / 1 * np.exp(-nbars)

def guess(xs, ys):
    mul = 1 if (xs[-1] > xs[0]) else -1
    amp = mul*(ys[-1]-ys[0])
    if amp < 0:
        ofs = np.max(ys)
    else:
        ofs = np.min(ys)
    tau = xs[-1] / 5
    return dict(
        n=0, amp=amp, ofs=ofs,
        alpha0=1.0, tau=tau,
    )