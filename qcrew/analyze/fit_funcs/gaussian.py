import numpy as np

def func(params, xs):
    x0 = params['x0'].value
    sig = params['sig'].value
    ofs = params['ofs'].value
    amp = params['amp'].value
    return ofs + amp * np.exp(-(xs - x0)**2 / (2 * sig**2))

def guess(xs, ys):
    ofs = (ys[0] + ys[-1]) / 2
    peak_idx = np.argmax(abs(ys - ofs))
    x0 = xs[peak_idx]
    sig = abs(xs[-1] - xs[0]) / 10
    amp = ys[peak_idx] - ofs
    yrange = np.max(ys) - np.min(ys)
    return {
        'x0': (x0, min(xs), max(xs)),
        'sig': (sig, abs(xs[1] - xs[0]), abs(xs[-1] - xs[0])),
        'ofs': (ofs, np.min(ys) - 0.3*yrange, np.max(ys) + 0.3*yrange),
        'amp': (amp, -3*yrange, 3*yrange),
    }
