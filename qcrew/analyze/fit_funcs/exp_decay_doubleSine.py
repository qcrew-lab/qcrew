import numpy as np

import qcrew.analyze.fit_funcs.sine as sine


def func(xs, amp=1, f0=0.05, phi=np.pi/4, ofs=0, tau=0.5, f1 = 0.05, relA = 0.):
    return amp/2 *(1+ np.exp(-xs / tau) * ( np.sin(2*np.pi*xs*f0 + phi) + relA * np.sin(2*np.pi*xs*(f1) + phi) ) ) + ofs

def guess(xs, ys):
    d = sine.guess(xs, ys)
    d['tau'] = (np.average(xs), 0, 10*xs[-1])
    d['f1'] = d['f0']
    d['relA'] = (0.,-1.,2.)
    return d
