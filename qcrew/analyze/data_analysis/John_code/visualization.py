from gates import *
import numpy as np
import qutip as qt
import matplotlib.pyplot as plt

plt.rcParams.update(
    {
        "figure.figsize": (11.7, 8.27),
        "font.size": 14,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

# taken from Alec Eickbusch
def plot_wigner(
    state,
    contour=False,
    fig=None,
    ax=None,
    max_alpha=2,
    cbar=False,
    npts=51,
    vmin=-1,
    vmax=1,
):

    xvec = np.linspace(-max_alpha, max_alpha, npts)
    W = qt.wigner(qt.ptrace(state, 1), xvec, xvec, g=2)
    if fig is None:
        fig = plt.figure(figsize=(6, 5))
    if ax is None:
        ax = fig.subplots()
    if contour:
        levels = np.linspace(-1.1, 1.1, 102)
        im = ax.contourf(
            xvec,
            xvec,
            W,
            cmap="seismic",
            vmin=vmin,
            vmax=vmax,
            levels=levels,
        )
    else:
        im = ax.pcolormesh(xvec, xvec, W, cmap="seismic", vmin=vmin, vmax=vmax)

    ax.set_xlabel(r"Re$(\alpha)$")
    ax.set_ylabel(r"Im$(\alpha)$")
    ax.grid()
    # ax.set_title(title)

    fig.tight_layout()
    if cbar:
        fig.subplots_adjust(right=0.8, hspace=0.25, wspace=0.25)
        # todo: ensure colorbar even with plot...
        # todo: fix this colorbar

        cbar_ax = fig.add_axes([0.85, 0.225, 0.025, 0.65])
        ticks = np.linspace(-1, 1, 5)
        fig.colorbar(im, cax=cbar_ax, ticks=ticks)
        cbar_ax.set_title(r"$\frac{\pi}{2} W(\alpha)$", pad=10)
    ax.set_aspect("equal", adjustable="box")

    def plot_qfunc(
        state,
        contour=False,
        fig=None,
        ax=None,
        max_alpha=2,
        cbar=False,
        npts=51,
    ):

        xvec = np.linspace(-max_alpha, max_alpha, npts)
        Q = qt.qfunc(qt.ptrace(state, 1), xvec, xvec, g=2)
        if fig is None:
            fig = plt.figure(figsize=(6, 5))
        if ax is None:
            ax = fig.subplots()
        if contour:
            levels = np.linspace(-1.1, 1.1, 102)
            im = ax.contourf(
                xvec,
                xvec,
                Q,
                cmap="seismic",
                vmin=-1,
                vmax=+1,
                levels=levels,
            )
        else:
            im = ax.pcolormesh(xvec, xvec, Q, cmap="seismic", vmin=-1, vmax=+1)

        ax.set_xlabel(r"Re$(\alpha)$")
        ax.set_ylabel(r"Im$(\alpha)$")
        ax.grid()
        # ax.set_title(title)

        fig.tight_layout()
        if cbar:
            fig.subplots_adjust(right=0.8, hspace=0.25, wspace=0.25)
            # todo: ensure colorbar even with plot...
            # todo: fix this colorbar

            cbar_ax = fig.add_axes([0.85, 0.225, 0.025, 0.65])
            ticks = np.linspace(-1, 1, 5)
            fig.colorbar(im, cax=cbar_ax, ticks=ticks)
            cbar_ax.set_title(r"$\frac{\pi}{2} W(\alpha)$", pad=10)
        ax.set_aspect("equal", adjustable="box")


def char_func_grid(state, xvec):
    """Calculate the Characteristic function as a 2Dgrid (xvec, xvec) for a given state.

    Args:
        state (Qobject): State of which we want to calc the charfunc
        xvec (_type_): array of displacements. The char func will be calculated for the grid (xvec, xvec)

    Returns:
        tuple(ndarray, ndarray): Re(char func), Im(char func)
    """
    cfReal = np.empty((len(xvec), len(xvec)))
    cfImag = np.empty((len(xvec), len(xvec)))
    N = state.dims[0][1]

    for i, alpha_x in enumerate(xvec):
        for j, alpha_p in enumerate(xvec):
            expect_value = qt.expect(
                qt.displace(N, alpha_x + 1j * alpha_p), qt.ptrace(state, 1)
            )
            cfReal[i, j] = np.real(expect_value)
            cfImag[i, j] = np.imag(expect_value)

    return cfReal, cfImag


def plot_char(
    state,
    max_alpha=3,
    npts=50,
    real=True,
    fig=None,
    ax=None,
    vmin=-1,
    vmax=1,
    cbar=False,
):

    xvec = np.linspace(-max_alpha, max_alpha, npts)
    CF_real, CF_imag = char_func_grid(state, xvec)

    if fig is None:
        fig = plt.figure(figsize=(6, 5))
    if ax is None:
        ax = fig.subplots()

    if real:
        im = ax.pcolormesh(
            xvec, xvec, (CF_real), cmap="bwr", vmin=vmin, vmax=vmax, shading="auto"
        )
        ax.set_aspect("equal")
        ax.set_xlabel(r"Re$(\alpha)$")
        ax.set_ylabel(r"Im$(\alpha)$")
        ax.set_title(r"$ Re(C(\alpha))$")
    else:

        im = ax.pcolormesh(
            xvec, xvec, (-CF_imag), cmap="bwr", vmin=vmin, vmax=vmax, shading="auto"
        )
        ax.set_aspect("equal")
        ax.set_xlabel(r"Re$(\alpha)$")
        ax.set_ylabel(r"Im$(\alpha)$")
        ax.set_title(r"$ Im(C(\alpha))$")

    if cbar:
        fig.subplots_adjust(right=0.8, hspace=0.25, wspace=0.25)
        # todo: ensure colorbar even with plot...
        # todo: fix this colorbar

        cbar_ax = fig.add_axes([0.85, 0.225, 0.025, 0.65])
        ticks = np.linspace(-1, 1, 5)
        fig.colorbar(im, cax=cbar_ax, ticks=ticks)


def char_func_grid_exp(
    state: qt.Qobj, xvec, t_displace: list, t_wait: list, epsilon, chi, loss, real=True
):
    ## t_displace, t_wait and epsilon have to be define outside such that we get an ECD(1) with alpha = 1
    cf = np.empty((len(xvec), len(xvec)))

    for i, alpha_x in enumerate(xvec):
        for j, alpha_p in enumerate(xvec):
            cf[i, j] = -char_point(
                state,
                t_displace,
                t_wait,
                -(alpha_x + 1j * alpha_p),
                epsilon,
                chi,
                loss,
                real=real,
            )  # added a minus sign to be consisten with experiment

    return cf


def plot_char_exp(
    state,
    t_displace,
    t_wait,
    epsilon,
    chi=CHI,
    loss=None,
    max_alpha=3,
    npts=50,
    real=True,
    fig=None,
    ax=None,
    cbar=False,
):

    xvec = np.linspace(-max_alpha, max_alpha, npts)

    CF = char_func_grid_exp(state, xvec, t_displace, t_wait, epsilon, chi, loss, real)

    if fig is None:
        fig = plt.figure(figsize=(6, 5))
    if ax is None:
        ax = fig.subplots()

    if real:
        im = ax.pcolormesh(
            xvec, xvec, (CF), cmap="bwr", vmin=-1, vmax=1, shading="auto"
        )
        ax.set_aspect("equal")
        ax.set_xlabel(r"Re$(\alpha)$")
        ax.set_ylabel(r"Im$(\alpha)$")
        ax.set_title(r"$ Re(C(\alpha))$")
    else:

        im = ax.pcolormesh(
            xvec, xvec, (-CF), cmap="bwr", vmin=-1, vmax=1, shading="auto"
        )
        ax.set_aspect("equal")
        ax.set_xlabel(r"Re$(\alpha)$")
        ax.set_ylabel(r"Im$(\alpha)$")
        ax.set_title(r"$ Im(C(\alpha))$")

    if cbar:
        fig.subplots_adjust(right=0.8, hspace=0.25, wspace=0.25)
        # todo: ensure colorbar even with plot...
        # todo: fix this colorbar

        cbar_ax = fig.add_axes([0.85, 0.225, 0.025, 0.65])
        ticks = np.linspace(-1, 1, 5)
        fig.colorbar(im, cax=cbar_ax, ticks=ticks)
        cbar_ax.set_title(r"$\frac{\pi}{2} W(\alpha)$", pad=10)


def plot_2D(xvec, yvec, char_func):
    fig, ax = plt.subplots(figsize=(10, 6))
    F = ax.pcolormesh(
        xvec, yvec, char_func, cmap="bwr", vmin=-1, vmax=1, shading="auto"
    )
    ax.set_aspect("equal")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    fig.colorbar(F)
    return
