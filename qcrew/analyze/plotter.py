""" Qcrew plotter v1.0 """

import matplotlib.pyplot as plt
import matplotlib.colors as colors
from qcrew.helpers import logger
from IPython import display
from qcrew.analyze import fit

COLOR_LIST = (
    "#0000FF",
    "#FF3300",
    "#2cde00",
    "#FF9933",
    "#663399",
    "#009966",
    "#66CCCC",
    "#000000",
)


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

        # If another figure has already been plotted, retrieve it and erase content
        self.fig = plt.gcf()
        self.fig.clear()

        self.hdisplay = display.display(self.fig, display_id=True)

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

        self.fig.clear()
        ax = self.fig.gca()

        # Determine how to plot the data
        if self.plot_setup["plot_type"] == "1D":

            # If only one independent variable, plot a single trace
            if len(independent_data) == 1:
                x_data = independent_data[0]
                z_data = dependent_data[0]
                try:
                    label = self.plot_setup["trace_labels"][0]
                except IndexError:
                    label = None
                self.plot_1D(x_data, z_data, fit_fn, label=label, err=err)

            # Plot a trace for each value in independent_data[1]
            if len(independent_data) == 2:
                x_data = independent_data[0]
                y_data = independent_data[1]
                z_data = dependent_data[0]
                for indx, trace_y in enumerate(y_data[0]):

                    # Pass user-defined label to the plot if provided, else pass
                    # y_value as a string
                    try:
                        label = self.plot_setup["trace_labels"][indx]
                    except IndexError:
                        label = str(trace_y)

                    # Get z data corresponding to this trace
                    z_trace_data = z_data[:, indx]
                    x_trace_data = x_data[:, indx]
                    err_trace_data = err[:, indx]

                    color = COLOR_LIST[indx]
                    self.plot_1D(
                        x_trace_data,
                        z_trace_data,
                        fit_fn,
                        label=label,
                        err=err_trace_data,
                        color=color,
                    )

            # Set plot parameters
            ax.set_ylabel(self.plot_setup["zlabel"])
            ax.legend()

        if self.plot_setup["plot_type"] == "2D":
            if len(independent_data) != 2:
                logger.error(f"2D sweeps require 2 independent variables")
                return

            x_data = independent_data[0]
            y_data = independent_data[1]
            z_data = dependent_data[0]

            self.plot_2D(x_data, y_data, z_data)

        # Set plot parameters
        ax.set_title(
            self.plot_setup["title"] + f": {n} repetition{'s' if n > 1 else ''}"
        )
        ax.set_xlabel(self.plot_setup["xlabel"])
        self.hdisplay.update(self.fig)

    def plot_2D(self, x, y, z):

        if self.plot_setup["zlog"]:
            if self.plot_setup["zlimits"]:
                vmin = self.plot_setup["zlimits"][0]
                vmax = self.plot_setup["zlimits"][1]
                norm = colors.LogNorm(vmin=vmin, vmax=vmax)
            else:
                norm = colors.LogNorm(vmin=z.min(), vmax=z.max())
        else:
            if self.plot_setup["zlimits"]:
                vmin = self.plot_setup["zlimits"][0]
                vmax = self.plot_setup["zlimits"][1]
                norm = colors.Normalize(vmin=vmin, vmax=vmax)
            else:
                norm = None

        ax = self.fig.gca()
        im = ax.pcolormesh(
            x, y, z, norm=norm, shading="auto", cmap=self.plot_setup["cmap"]
        )
        cbar = self.fig.colorbar(im)
        # Set plot parameters
        ax.set_ylabel(self.plot_setup["ylabel"])
        cbar.set_label(self.plot_setup["zlabel"])

    def plot_1D(self, x, z, fit_fn, label=None, err=None, color="b"):

        ax = self.fig.gca()

        # plot the data
        label = label or "data"
        if err is not None and self.plot_setup["plot_err"]:
            self.plot_errorbar(x, z, ax, err, label, color=color)
        else:
            self.plot_scatter(x, z, ax, label, color=color)

        if fit_fn:
            # plot the fit curve
            fit_text, fit_z = self.fit(x, z, fit_fn=fit_fn)
            left = 0
            bottom = -0.1
            ax.text(
                left,
                bottom,
                fit_text,
                horizontalalignment="left",
                verticalalignment="top",
                transform=ax.transAxes,
            )

            if self.plot_setup["zlog"]:
                ax.set_yscale("log")

            self.plot_line(x, fit_z, ax, label="fit", color=color)

        if self.plot_setup["zlimits"]:
            ax.set_ylim(self.plot_setup["zlimits"])

    def plot_errorbar(self, x, z, axis, zerr, label, color="b"):
        axis.errorbar(
            x,
            z,
            yerr=zerr,
            label=label,
            ls="none",
            lw=1,
            ecolor=color,
            color=color,
            marker="o",
            ms=4,
            mfc=color,
            mec=color,
            capsize=3,
            fillstyle="none",
        )

    def plot_scatter(self, x, z, axis, label, color="b"):
        axis.scatter(x, z, s=4, color=color, marker="o", label=label)

    def plot_line(self, x, z, axis, label, color="b"):
        axis.plot(x, z, color=color, lw=2, label=label)
