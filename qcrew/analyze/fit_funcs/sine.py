import numpy as np

def func(xs, f0, ofs, amp, phi):
    return ofs + amp * np.sin(2*np.pi*f0*xs + phi)

def guess(xs, ys):
    fs = np.fft.rfftfreq(len(xs), xs[1] - xs[0])
    ofs = np.mean(ys)
    fft = np.fft.rfft(ys - ofs)
    idx = np.argmax(abs(fft))
    f0 = fs[idx]
    amp = np.std(ys - ofs)
    phi = np.angle(fft[idx])
    return {
        'f0': (f0, fs[0], fs[-1]),
        'ofs': (ofs, np.min(ys), np.max(ys)),
        'amp': (amp, 0, np.max(ys) - np.min(ys)),
        'phi': (phi, -2*np.pi, 2*np.pi),
    }
