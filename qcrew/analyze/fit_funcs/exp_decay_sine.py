import numpy as np

import qcrew.analyze.fit_funcs.sine as sine


def func(xs, amp=1, f0=0.05, phi=np.pi/4, ofs=0, tau=0.5):
    return amp * np.sin(2*np.pi*xs*f0 + phi) * np.exp(-xs / tau) + ofs

def guess(xs, ys):
    d = sine.guess(xs, ys)
    d['tau'] = (np.average(xs), 0, 10*xs[-1])
    return d
