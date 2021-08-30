""" Qcrew plotter v1.0 """

import matplotlib.pyplot as plt
from IPython import display
from qcrew.analyze import fit
import matplotlib as mpl
from matplotlib import colors 

class Plotter:
    """Single axis x-y plotter. Supports line, scatter, and errorbar plot. Provides a rudimentary live plotting routine."""

    def __init__(self, plot_setup):

        # matplotlib config
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
        
        # plot setup
        self.plot_setup = plot_setup

        # subplots 
        if "nrows" in plot_setup and "ncols" in plot_setup: 
            self.nrows = plot_setup["nrows"]
            self.ncols = plot_setup["ncols"]
        else: 
            self.nrows = 1
            self.ncols = 1
        
        #suptitle
        if "suptitle" in plot_setup:
            self.title = plot_setup["suptitle"]

        self.create_subplot()

    def create_subplot(self):
        self.fig, self.axs = plt.subplots(self.nrows, self.ncols)
        self.hdisplay = display.display(self.fig, display_id=True)
        self.fig.suptitle(self.title)

    @staticmethod
    def fit(x, y, fit_func) -> tuple:
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
    
    def live_1dplot(
            self,
            ax,
            independent_data,
            dependent_data,
            n,
            fit_func=None,
            errbar=None,
        ):
        
        ax.clear()

        if "plot_type" in self.plot_setup:
            plot_type = self.plot_setup["plot_type"]
        else:
            plot_type = "scatter"

        if len(independent_data) == 1 and len(dependent_data) == 1:
            x = independent_data[0]
            y = dependent_data[0]
            try:
                label = self.plot_setup["trace_labels"]
            except IndexError:
                label = None

            self.plot_1d(ax, x, y, 
                        plot_type=plot_type,
                        fit_func=fit_func,
                        errbar=errbar, 
                        label=label)
        
        elif len(independent_data) == 2:
            x = independent_data[0]
            label_data = independent_data[1]

            for index, trace in enumerate(label_data):
                try:
                    label = self.plot_setup["trace_labels"] + str(trace)
                except IndexError:
                    label = str(trace)

                y = dependent_data[index]
                self.plot_1d(ax, x, y, 
                        plot_type=plot_type,
                        fit_func=fit_func,
                        errbar=errbar, 
                        label=label)
             

        ax.set_title(self.title + f": {n} repetition{'s' if n > 1 else ''}")
        ax.set_xlabel(self.plot_setup["xlabel"])
        ax.set_ylabel(self.plot_setup["zlabel"])
        ax.legend()
        
        self.hdisplay.update(self.fig)

    
    def plot_1d(self, ax, x, y, plot_type ="scatter",fit_func=None, errbar=None, label=None):
        if plot_type == "scatter":
            if errbar is not None:
                self.plot_errorbar(ax, x, y, errbar, label)
            else:
                self.plot_scatter(ax, x, y, errbar, label)
        
        elif plot_type  == "line":
            self.plot_line(ax, x, y, label)

        if fit_func:
            # plot the fit curve
            fit_text, fit_y = Plotter.fit(x, y, fit_func=fit_func)
        
            # fit text position 
            left = 0
            bottom = -0.1
            self.ax.text(
                left,
                bottom,
                fit_text,
                horizontalalignment="left",
                verticalalignment="top",
                transform=self.ax.transAxes)

            self.plot_line(ax, x, fit_y,  label="fit of" +label, color="r")


    def plot_errorbar(self, ax, x, y, yerr, label):
        mpl.rcParams["errorbar.capsize"] = 3 
        mpl.rcParams["errorbar.ls"] = "none" 
        mpl.rcParams["errorbar.ecolor"] = "b"
        mpl.rcParams["errorbar.lw"] = 1
        mpl.rcParams["errorbar.marker"] = "o"
        mpl.rcParams["errorbar.ms"] = 4 
        mpl.rcParams["errorbar.mfc"] = "b"
        mpl.rcParams["errorbar.mec"] = "b"
        mpl.rcParams["errorbar.fillstyle"] = "none"

        ax.errorbar(x, y, yerr=yerr, label=label)

    def plot_scatter(self, ax, x, y, label):
        mpl.rcParams["scatter.s"] = 4
        mpl.rcParams["scatter.color"] = "b"
        mpl.rcParams["scatter.marker"] = "o"

        ax.scatter(x, y, label=label)

    def plot_line(self, ax, x, y, label, color="b"):
        ax.plot(x, y, color=color, lw=2, label=label)

    def live_2dplot(self,
                    ax,
                    independent_data,
                    dependent_data,
                    n):
            
        ax.clear()
        
        x = independent_data[0]
        y = independent_data[1]
        z = dependent_data[0]

        vmin = min(z)
        vmax = max(z)
        norm = colors.LogNorm(vmin=vmin, vmax=vmax)

        if "cmap" in self.plot_setup: 
            mpl.rcParams["pcolormesh.cmap"] = self.plot_setup["cmap"]
        else:
            mpl.rcParams["pcolormesh.cmap"] = "terrain"
        
        if "norm" in self.plot_setup: 
            mpl.rcParams["pcolormesh.norm"] = self.plot_setup["norm"]
        else:
            mpl.rcParams["pcolormesh.norm"] = norm

        if self.plot_setup["plot_setup"] == "pcolormesh": 
            im = ax.pcolormesh(x, y, (z), shading="auto")

        if "colorbar"in self.plot_setup:
            if self.plot_setup["colorbar"] == True: 
                cbar = self.fig.colorbar(im, ax=ax, orientation="vertical", fraction=.1, pad =0.023)
            
                if "colorbar_label" in self.plot_setup:
                    colorbar_label = self.plot_setup["colorbar_label"] 
                    cbar.set_label(colorbar_label)
        
        self.ax.set_title(self.plot_setup["title"] + f": {n} repetition{'s' if n > 1 else ''}")
        self.ax.set_xlabel(self.plot_setup["xlabel"])
        self.ax.set_ylabel(self.plot_setup["ylabel"])

        self.hdisplay.update(self.fig)


