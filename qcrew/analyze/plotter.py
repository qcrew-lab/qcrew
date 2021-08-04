""" Qcrew plotter v1.0 """

import matplotlib.pyplot as plt
from IPython import display
from qcrew.analyze import fit


class Plotter:
    """Single axis x-y plotter. Supports line, scatter, and errorbar plot. Provides a rudimentary live plotting routine."""

    def __init__(self, title: str, xlabel: str, ylabel: str = "Signal (A.U.)"):

        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel

        plt.rcParams["figure.figsize"] = (9, 6)  # in inches by default
        plt.rcParams["axes.linewidth"] = 1
        plt.rcParams["xtick.major.size"] = 1
        plt.rcParams["ytick.major.size"] = 1
        plt.rcParams["xtick.minor.size"] = 0.5
        plt.rcParams["ytick.minor.size"] = 0.5
        plt.rcParams["legend.frameon"] = True
        plt.rcParams["legend.loc"] = "best"
        plt.rcParams["xtick.major.width"] = 1
        plt.rcParams["ytick.major.width"] = 1
        plt.rcParams["xtick.minor.width"] = 0.5
        plt.rcParams["ytick.minor.width"] = 0.5
        plt.rcParams["font.sans-serif"] = "Arial"
        plt.rcParams["font.size"] = 12
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["legend.fontsize"] = 12

        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.hdisplay = display.display("", display_id=True)

    def fit(self, xs, ys, fit_func) -> tuple:

        # get fit parameters
        params = fit.do_fit(fit_func, xs, ys)
        fit_ys = fit.eval_fit(fit_func, params, xs)

        # convert param values into formated string
        param_val_list = [
            key + " = {:.3e}".format(val.value) for key, val in params.items()
        ]
        # Join list in a single block of text
        fit_text = "\n".join(param_val_list)

        return fit_text, fit_ys

    def live_plot(
        self,
        x,
        y,
        n,
        label=None,
        fit_fn=None,
        err=None,
        plot_type="scatter",
    ):
        """ " If `live_plot(data)` is called in an IPython terminal context, the axis is refreshed and plotted with the new data using IPython `display` tools."""

        self.ax.clear()
        # plot the data
        label = label or "data"
        if plot_type == "scatter":
            if err is not None:
                self.plot_errorbar(x, y, self.ax, err, label)
            else:
                self.plot_scatter(x, y, self.ax, label)
        elif plot_type == "line":
            self.plot_line(x, y, self.ax, label)

        if fit_fn:
            # plot the fit curve
            fit_text, fit_y = self.fit(x, y, fit_func=fit_fn)
            left = 0
            bottom = -0.1
            self.ax.text(
                left,
                bottom,
                fit_text,
                horizontalalignment="left",
                verticalalignment="top",
                transform=self.ax.transAxes,
            )
            self.plot_line(x, fit_y, self.ax, label="fit", color="r")

        self.ax.set_title(self.title + f": {n} repetition{'s' if n > 1 else ''}")
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.legend()

        self.hdisplay.update(self.fig)

    def plot_errorbar(self, x, y, axis, yerr, label: str):
        axis.errorbar(
            x,
            y,
            yerr=yerr,
            label=label,
            ls="none",
            lw=1,
            ecolor="b",
            marker="o",
            ms=4,
            mfc="b",
            mec="b",
            capsize=3,
            fillstyle="none",
        )

    def plot_scatter(self, x, y, axis, label):
        axis.scatter(x, y, s=4, color="b", marker="o", label=label)

    def plot_line(self, x, y, axis, label, color="b"):
        axis.plot(x, y, color=color, lw=2, label=label)
