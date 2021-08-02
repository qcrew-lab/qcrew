import numpy as np

import qcrew.codebase.analysis.fit_funcs.sine as sine


def func(xs, amp=1, tau=1e5, f0=5e-5, phi=np.pi/4, ofs=0.1, ht=0.05, tH=1e6):
    return (0.5 * amp * np.exp(-xs / tau) * (1 + np.sin(2*np.pi*xs*f0 + phi) ) ) + ofs + ht * (1 - np.exp(-xs / tH))

def guess(xs, ys):
    d = sine.guess(xs, ys)
    d['tau'] = (np.average(xs), 0, 10*xs[-1])
    d['ht'] = (0.05, 0, 1)
    d['tH'] = (np.average(xs), 0, 10*xs[-1])
    return d
