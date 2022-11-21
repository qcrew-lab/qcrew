import numpy as np

import qcrew.analyze.fit_funcs.sine as sine


def func(
    xs, amp=1, kappa=1, chi=1, Gamma_2=1 / 21, delta=0.5, phi_0=10, n_0=2, ofs=0.5
):
    tau = (1 - np.exp(-(kappa + chi * 1j) * xs)) / (kappa + 1j * chi)
    return (
        amp
        * (
            1
            - (
                np.exp(-(Gamma_2 + 1j * delta) * xs + (phi_0 - n_0 * chi * tau) * 1j)
            ).imag
        )
        + ofs
    )


def guess(xs, ys):
    ofs = np.mean(ys)
    peak_idx = np.argmax(abs(ys - ofs))
    amp = ys[peak_idx] - ofs
    kappa = 1  # hard coded in, can be varied
    chi = 1
    Gamma_2 = 1 / 21
    delta = 0.5
    phi_0 = ys[0]
    n_0 = 1
    skywalker = {
        "amp": (amp, 0, np.max(ys) - np.min(ys)),
        "kappa": (kappa, kappa - 0.01, kappa + 0.01),
        "chi": (chi, chi - 0.01, chi + 0.01),
        "Gamma_2": (Gamma_2, Gamma_2 - 0.01, Gamma_2 + 0.01),
        "delta": (delta, delta - 0.01, delta + 0.01),
        "phi_0": (phi_0, -np.pi, np.pi),
        "n_0": (n_0, 0, 10),
        "ofs": (ofs, np.min(ys), np.max(ys)),
    }
    return skywalker
