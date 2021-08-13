""" Qcrew plotter v1.0 """

import matplotlib.pyplot as plt
from qcrew.helpers import logger
from IPython import display
from qcrew.analyze import fit


class Plotter:
    """Single axis x-y plotter. Supports line, scatter, and errorbar plot. Provides a rudimentary live plotting routine."""

    def __init__(self, plot_setup):
        """
        Plot setup is a dictionary with user-defined parameters for plotting such as axis labels, title, plot type etc.
        """

        self.plot_setup = plot_setup

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

    def fit(self, xs, ys, fit_fn) -> tuple:

        # get fit parameters
        params = fit.do_fit(fit_fn, xs, ys)
        fit_ys = fit.eval_fit(fit_fn, params, xs)

        # convert param values into formated string
        param_val_list = [
            key + " = {:.3e}".format(val.value) for key, val in params.items()
        ]
        # Join list in a single block of text
        fit_text = "\n".join(param_val_list)

        return fit_text, fit_ys

    def live_plot(
        self,
        independent_data,
        dependent_data,
        n,
        fit_fn=None,
        err=None,
    ):
        """
        If `live_plot(data)` is called in an IPython terminal context, the axis is refreshed and plotted with the new data using IPython `display` tools.
        This version of the plotter assumes 1 dependent variable and up to 2 independent variables.
        """

        self.ax.clear()

        # Determine how to plot the data
        if self.plot_setup["plot_type"] == "1D":

            # If only one independent variable, plot a single trace
            if len(independent_data) == 1:
                x_data = independent_data[0]
                z_data = dependent_data[0]
                label = self.plot_setup["trace_labels"][0]
                self.plot_1D(x_data, z_data, n, fit_fn, label=label, err=err)

            # Plot a trace for each value in independent_data[1]
            if len(independent_data) == 2:
                x_data = independent_data[0]
                y_data = independent_data[1]
                z_data = dependent_data[0]
                for indx, trace_y in enumerate(y_data):

                    # Pass user-defined label to the plot if provided, else pass
                    # y_value as a string
                    try:
                        label = self.plot_setup["trace_labels"][indx]
                    except IndexError:
                        label = str(trace_y)

                    # Get z data corresponding to this trace
                    z_trace_data = z_data[:, indx]
                    self.plot_1D(x_data, z_trace_data, n, fit_fn, label=label, err=err)

        if self.plot_setup["plot_type"] == "2D":
            if len(independent_data) != 2:
                logger.error(f"2D sweeps require 2 independent variables")
                return

            self.plot_2D(x_data, y_data, z_data)

    def plot_1D(self, x, z, n, fit_fn, label=None, err=None):

        # plot the data
        label = label or "data"
        if err is not None and self.plot_setup["plot_err"]:
            self.plot_errorbar(x, z, self.ax, err, label)
        else:
            self.plot_scatter(x, z, self.ax, label)

        if fit_fn:
            # plot the fit curve
            fit_text, fit_z = self.fit(x, z, fit_fn=fit_fn)
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
            self.plot_line(x, fit_z, self.ax, label="fit", color="r")

        self.ax.set_title(self.title + f": {n} repetition{'s' if n > 1 else ''}")
        self.ax.set_xlabel(self.plot_setup["xlabel"])
        self.ax.set_ylabel(self.plot_setup["zlabel"])
        self.ax.legend()

        self.hdisplay.update(self.fig)

    def plot_errorbar(self, x, z, axis, yerr, label: str):
        axis.errorbar(
            x,
            z,
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

    def plot_scatter(self, x, z, axis, label):
        axis.scatter(x, z, s=4, color="b", marker="o", label=label)

    def plot_line(self, x, z, axis, label, color="b"):
        axis.plot(x, z, color=color, lw=2, label=label)
