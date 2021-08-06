""" Qcrew plotter v1.0 """

import matplotlib.pyplot as plt
from IPython import display
from qcrew.analyze import fit
import matplotlib as mpl
from matplotlib import colors 

class Plotter:
    """Single axis x-y plotter. Supports line, scatter, and errorbar plot. Provides a rudimentary live plotting routine."""

    def __init__(self, title: str, xlabel: str, ylabel: str = "Signal (A.U.)"):

        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.hdisplay = display.display("", display_id=True)

        mpl.rcParams["figure.figsize"] = (9, 6)  # in inches by default
        mpl.rcParams["axes.linewidth"] = 1
        mpl.rcParams["xtick.major.size"] = 1
        mpl.rcParams["ytick.major.size"] = 1
        mpl.rcParams["xtick.minor.size"] = 0.5
        mpl.rcParams["ytick.minor.size"] = 0.5
        mpl.rcParams["legend.frameon"] = True
        mpl.rcParams["legend.loc"] = "best"
        mpl.rcParams["xtick.major.width"] = 1
        mpl.rcParams["ytick.major.width"] = 1
        mpl.rcParams["xtick.minor.width"] = 0.5
        mpl.rcParams["ytick.minor.width"] = 0.5
        mpl.rcParams["font.sans-serif"] = "Arial"
        mpl.rcParams["font.size"] = 12
        mpl.rcParams["axes.labelsize"] = 12
        mpl.rcParams["legend.fontsize"] = 12

    def fit(self, x, y, fit_func) -> tuple:
        """
        Args:
        x: x axis values
        y: y axis values
        fit_func: the name of fit funciton

        Return:
        fit_text: a string text containing the fit parameters which is shown in the figure
        fit_y： the fitted y axis values 

        """

        # get fit parameters
        params = fit.do_fit(fit_func, x, y)

        # get the fitted y trace 
        fit_y = fit.eval_fit(fit_func, params, x)

        # convert param values into formated strings
        param_val_list = [
            key + " = {:.3e}".format(val.value) for key, val in params.items()
        ]
        # Join list in a single block of text
        fit_text = "\n".join(param_val_list)

        return fit_text, fit_y, params
    
    def live_2dplot(self, x, y, z, plot_type="pcolormesh", cmap="terrain", colorbar=True, colorbar_label=""):

        self.ax.clear()
        vmin = min(z)
        vmax = max(z)
        norm = colors.LogNorm(vmin=vmin, vmax=vmax)
        mpl.rcParams["pcolormesh.cmap"] = cmap
        mpl.rcParams["pcolormesh.norm"] = norm

        if plot_type == "pcolormesh":
            im = self.ax.pcolormesh(x, y, (z))
        
        if colorbar:
            cbar = self.fig.colorbar(im, ax=self.ax, orientation="vertical", fraction=.1, pad =0.023)
            cbar.set_label(colorbar_label)
        
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)

        self.hdisplay.update(self.fig)

    def live_plot(self, x, y, n, label=None, fit_func=None, errorbar=None, plot_type="scatter"):
        """  If `live_plot(data)` is called in an IPython terminal context, the axis is refreshed and plotted with the new data using IPython `display` tools.

        Args:
        x: x axis values
        y: y axis values
        n: repetition number so far
        label: trace label
        fit_func: the name of fit function, the default is "None" representing that the fit trace is not displayed 
        errorbar: the errorbar of y axis value, the default is "None" representing that the errorbar in y axis is not displayed 
        plot_type: either "scatter" or "line"
        
        """
        # clear the figure 
        self.ax.clear()

        # plot the data
        label = label or "data"
        if plot_type == "scatter":
            if errorbar is not None:
                self.plot_errorbar(x, y, self.ax, errorbar, label:str)
            else:
                self.plot_scatter(x, y, self.ax, label)
        elif plot_type == "line":
            self.plot_line(x, y, self.ax, label)

        if fit_func:
            # plot the fit curve
            fit_text, fit_y = self.fit(x, y, fit_func=fit_func)
            
            # fit text position 
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

        mpl.rcParams["errorbar.capsize"] = 3 
        mpl.rcParams["errorbar.ls"] = "none" 
        mpl.rcParams["errorbar.ecolor"] = "b"
        mpl.rcParams["errorbar.lw"] = 1
        mpl.rcParams["errorbar.marker"] = "o"
        mpl.rcParams["errorbar.ms"] = 4 
        mpl.rcParams["errorbar.mfc"] = "b"
        mpl.rcParams["errorbar.mec"] = "b"
        mpl.rcParams["errorbar.fillstyle"] = "none"

        axis.errorbar(x, y, yerr=yerr, label=label)

    def plot_scatter(self, x, y, axis, label):
        mpl.rcParams["scatter.s"] = 4
        mpl.rcParams["scatter.color"] = "b"
        mpl.rcParams["scatter.marker"] = "o"

        axis.scatter(x, y, label=label)

    def plot_line(self, x, y, axis, label, color="b"):
        axis.plot(x, y, color=color, lw=2, label=label)
