import numpy as np

# Note: we scale the fit_function
def func(xs, f0, ofs, amp, scale=2):
    return ofs + amp * np.cos(2 * scale * f0 * xs) * np.exp(
        -np.abs(scale * xs) ** 2 / 2
    )


# if we add the imag part to the fit_function
# def func(xs, f0, ofs, amp):
#     return ofs + amp * np.cos(2 * np.real(f0) * np.imag(xs) - np.imag(f0) * np.real(xs)) * np.exp(-np.abs(xs)**2 / 2)


def guess(xs, ys):
    fs = np.fft.rfftfreq(len(xs), xs[1] - xs[0])
    ofs = np.mean(ys)
    fft = np.fft.rfft(ys - ofs)
    idx = np.argmax(abs(fft))
    f0 = fs[idx]
    amp = np.std(ys - ofs)
    # phi = np.angle(fft[idx])
    return {
        "f0": (f0, fs[0], fs[-1]),
        "ofs": (ofs, np.min(ys), np.max(ys)),
        "amp": (amp, 0, np.max(ys) - np.min(ys)),
        # 'phi': (phi, -2*np.pi, 2*np.pi),
    }
