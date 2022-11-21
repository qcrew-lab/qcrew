# general packages
from fileinput import filename
from qcrew.helpers.parametrizer import Parametrized
from qcrew.helpers import logger
import qcrew.measure.qua_macros as macros
from typing import ClassVar
import numpy as np
import abc
import lmfit

# qua modules
from qm import qua


class Experiment(Parametrized):
    """
    Abstract class for experiments using QUA sequences.
    """

    # logger.info(f"Created {self}")
    _parameters: ClassVar[set[str]] = {
        "mode_names",  # names of the modes used in the experiment
        "reps",  # number of times the experiment is repeated
        "wait_time",  # wait time in nanoseconds between repetitions
        "fetch_period",  # wait time between fetching and plotting
        "single_shot",
    }

    def __init__(
        self,
        modes,
        reps,
        wait_time,
        x_sweep=None,
        y_sweep=None,
        fetch_period=1,
        single_shot=False,
        plot_quad=None,
        cable_delay=0,
        extra_vars: dict[str, macros.ExpVariable] = None,
    ):

        # List of modes used in the experiment. String values will be replaced by
        # corresponding modes by the professor module.
        self.modes = modes

        # Experiment loop variables
        self.reps = reps
        self.wait_time = wait_time

        # Wait time between live fetching/plotting/saving rounds
        self.fetch_period = fetch_period

        # Sweep configurations
        self.sweep_config = {"n": (0, self.reps, 1), "x": x_sweep, "y": y_sweep}
        self.buffering = tuple()  # defined in _configure_sweeps

        # Is single-shot being used?
        self.single_shot = single_shot

        # Should plot quadratures instead of Z_AVG?
        self.plot_quad = plot_quad

        # cable delay calibration for phase measurements
        self.cable_delay = cable_delay

        # ExpVariable definitions. This list is updated in _configure_sweeps and after
        # stream and variable declaration.
        self.variables = {
            "n": macros.ExpVariable(var_type=int, sweep=self.sweep_config["n"]),
            "x": macros.ExpVariable(average=False, save_all=False),
            "y": macros.ExpVariable(average=False, save_all=False),
            "I": macros.ExpVariable(
                average=False, tag="I", var_type=qua.fixed, buffer=True
            ),
            "Q": macros.ExpVariable(
                average=False, tag="Q", var_type=qua.fixed, buffer=True
            ),
        }

        # Single shot
        if self.single_shot:
            self.variables |= {
                "state": macros.ExpVariable(
                    average=True,
                    tag="state",
                    var_type=qua.fixed,
                    buffer=True,
                    save_all=False,
                )
            }

        if extra_vars is not None:
            self.variables |= extra_vars
        # Extra memory tags for saving server-side stream operation results
        self.Z_SQ_RAW_tag = "Z_SQ_RAW"
        self.Z_SQ_RAW_AVG_tag = "Z_SQ_RAW_AVG"
        self.Z_AVG_tag = "Z_AVG"

        # tags of the data to be used in the standard deviation estimation
        self.sd_estimation_tags = [self.Z_SQ_RAW_tag, self.Z_SQ_RAW_AVG_tag]

        # tags of the data to be used in live saving
        self.live_saving_tags = [self.variables["I"].tag, self.variables["Q"].tag]

        # tags of the data to be used in the final save
        self.final_saving_tags = [self.Z_AVG_tag] + [
            self.variables[v].tag for v in ["x", "y"] if self.variables[v].tag
        ]

        # filename and path where data is saved
        self._filename = None

        # parameters to be used by the plotter. Updated in self.setup_plot method.
        self.plot_setup = dict()
        self.setup_plot(**self.plot_setup)

        logger.info(f"Created {type(self).__name__}")

    @property
    def filename(self):
        # Return filename where experiment data is saved
        return self._filename

    @filename.setter
    def filename(self, f):
        # Set filename where experiment data is saved
        # Set plot_setup["title"] as filename + experiment name if no other title is
        # set.

        self._filename = f

        if not self.plot_setup["title"]:
            self.plot_setup["title"] = self._filename + "\n" + self.name

        return

    @property
    def mode_names(self):
        # return the name of each mode object in self.modes
        # Assumes the professor has already updated self.modes
        return [mode.name for mode in self.modes]

    @property
    def results_tags(self):
        # return the tags for independent variables x, y (if applicable) and dependent
        # variables z for live plotting and data saving.

        indep_tags = []
        for var in ["x", "y"]:
            if self.variables[var].tag:
                indep_tags.append(self.variables[var].tag)

        # TODO: implement more than 1 dependent variable (multiple readout)
        if self.plot_quad:
            dep_tags = [self.plot_quad]

        elif self.single_shot:
            dep_tags = ["state"]
        else:
            dep_tags = [self.Z_AVG_tag]

        return indep_tags, dep_tags

    def setup_plot(
        self,
        xlabel=None,
        ylabel=None,
        zlabel=None,
        trace_labels=[],
        title=None,
        skip_plot=False,
        plot_type="1D",
        plot_err=True,
        cmap="viridis",
        zlimits=None,
        zlog=False,
    ):
        """
        Updates self.plot_setup dictionary with the parameters to be used by the
        plotter.

        The x and y labels are set up independently if the corresponding sweep exists.

        plot_type identifies how the plotter should arrange the data. If "1D" and x,y
        sweeps are configured, one x sweep trace is plotted for every value of y. If
        the user wants to plot a colormesh instead, pass plot_type = '2D'.

        trace_labels is a list of labels for each trace. If plot_type = "1D" and a y
        sweep is
        configured, each label will correspond to a value of y.

        plot_err toggles errorbar plotting.

        """

        # title is updated later with the filename, experiment name and number of
        # repetitions
        if not title:
            title = ""

        if not zlabel:
            zlabel = "P1" if self.single_shot else "Signal (a.u.)"
        if not zlimits:
            zlimits = (-0.05, 1.05) if self.single_shot and not zlog else None

        self.plot_setup = {
            "xlabel": xlabel,
            "ylabel": ylabel,
            "zlabel": zlabel,
            "trace_labels": trace_labels,
            "title": title,
            "skip_plot": skip_plot,
            "plot_type": plot_type,
            "plot_err": plot_err,
            "cmap": cmap,
            "zlimits": zlimits,
            "zlog": zlog,
        }

        return

    def _configure_sweeps(self, sweep_variables_keys):
        """
        Check if each x and y sweeps are correctly configured. If so, update buffering, variable type, and tag of x and y in self.variables accordingly.
        """

        buffering = list()
        for key in sweep_variables_keys:
            # Set its sweep according to user-defined configurations
            if self.sweep_config[key]:
                self.variables[key].configure_sweep(self.sweep_config[key])

                # Log the type of sweep configured
                if self.variables[key].sweep_type == "for_":
                    logger.info(f"Configured linear sweep on variable {key}")
                if self.variables[key].sweep_type == "for_each_":
                    logger.info(
                        f"Configured sweep with arbitrary values on variable {key}"
                    )

                # Update buffering
                buffering.append(self.variables[key].buffer_len)
                # Flag for buffering in stream processing
                self.variables[key].buffer = True
                # Define key as memory tag
                self.variables[key].tag = key

        # if an internal sweep is defined in the child experiment class, add its length
        # to the buffering
        try:
            buffering.append(len(self.internal_sweep))
        except AttributeError:
            pass

        self.buffering = tuple(buffering)

        if len(self.buffering) == 0:
            logger.warning("No sweep is configured")

        logger.info(f"Set buffer dimensions: {self.buffering}")
        return

    @abc.abstractmethod
    def QUA_play_pulse_sequence(self):
        """
        Macro that defines the QUA pulse sequence inside the experiment loop. It is
        specified by the experiment (spectroscopy, power rabi, etc.) in the child class.
        """
        pass

    @abc.abstractmethod
    def data_analysis(self, params):
        """
        (XGH)
        Makes PhD student stupidier. Manipulates the fit parameters as defined in the
        child experiment class and spits out another set of parameters.
        """
        raise NotImplementedError

    def QUA_sequence(self):
        """
        Method that returns the QUA sequence to be executed in the quantum machine.
        The x sweep is always the innermost loop when both x and y are configured.
        """

        self._configure_sweeps(["x", "y"])

        with qua.program() as qua_sequence:

            # Initial variable and stream declarations
            self.variables = macros.declare_variables(self.variables)
            self.variables = macros.declare_streams(self.variables)

            # Stores QUA variables as attributes for easy use
            for key, value in self.variables.items():
                setattr(self, key, value.var)
            # Plays pulse sequence in a loop. Variable order defines loop nesting order
            sweep_variables = [self.variables[key] for key in ["n", "x", "y"]]
            macros.QUA_loop(self.QUA_play_pulse_sequence, sweep_variables)

            # Define stream processing
            buffer_len = np.prod(self.buffering)
            with qua.stream_processing():
                macros.process_streams(self.variables, buffer_len=buffer_len)
                macros.process_Z_values(
                    self.variables["I"].stream,
                    self.variables["Q"].stream,
                    buffer_len=buffer_len,
                )

        return qua_sequence

    def QUA_stream_results(self):
        """
        Execute stream_results macro in macros library. Meant to be used in
        self.QUA_play_pulse_sequence.
        """
        macros.stream_results(self.variables)

    def estimate_sd(self, statistician, partial_results, num_results, stderr):
        """
        Method to call the statistician and estimate running mean standard error.
        stderr holds the running values of (stderr, mean, variance * (n-1))
        """

        # TODO do this for multiple dependent variables

        zs_raw = np.sqrt(partial_results[self.Z_SQ_RAW_tag])
        zs_raw_avg = np.sqrt(partial_results[self.Z_SQ_RAW_AVG_tag])

        stderr = statistician.get_std_err(zs_raw, zs_raw_avg, num_results, *stderr)

        return stderr
    
    def get_raw_results(self):
        return "checking"

    def plot_results(self, plotter, partial_results, num_results, stderr):
        """
        Retrieves, reorganizes the data and sends it to the plotter.
        """

        indep_tags, dep_tags = self.results_tags

        independent_data = []
        for tag in indep_tags:
            reshaped_data = partial_results[tag].reshape(self.buffering)
            independent_data.append(reshaped_data)

        dependent_data = []
        for tag in dep_tags:

            if tag == "Z_AVG":
                # Take the square root of Z_AVG variables. This step is required for
                # dependent values calculated as I^2 + Q^2 in stream processing.
                data = np.sqrt(partial_results[tag])
            elif tag == "PHASE":
                freqs = independent_data[0]
                data = np.average(
                    partial_results["I"] + 1j * partial_results["Q"], axis=0
                )
                data = np.unwrap(np.angle(data))
                data -= freqs * self.cable_delay
            else:
                data = partial_results[tag]

            # Reshape the fetched data with buffer lengths
            reshaped_data = data.reshape(self.buffering)
            dependent_data.append(reshaped_data)

        try:
            internal_sweep = self.internal_sweep
            # Repeat the values
            for indx in range(len(self.buffering) - 1):
                internal_sweep = [internal_sweep] * self.buffering[indx]

            independent_data.append(internal_sweep)
            internal_sweep_dict = {"internal sweep": internal_sweep}
        except AttributeError:
            internal_sweep_dict = {}
            pass

        # Estimate standard error
        if self.single_shot and self.plot_setup["plot_err"]:
            # Variance of the binomial variable assuming our estimate for probabilities
            # are accurate.
            error_data = np.sqrt(
                dependent_data[0] * (1 - dependent_data[0]) / num_results
            )

        elif self.plot_setup["plot_err"]:
            # Retrieve and reshape standard error estimation
            error_data = stderr[0].reshape(self.buffering)

        else:
            error_data = None

        if not self.plot_setup["skip_plot"]:
            plotter.live_plot(
                independent_data,
                dependent_data,
                num_results,
                fit_fn=self.fit_fn,
                err=error_data,
                data_analysis=self.data_analysis,
            )

        # build data dictionary for final save
        dep_data_dict = {dep_tags[i]: dependent_data[i] for i in range(len(dep_tags))}
        indep_data_dict = {
            indep_tags[i]: independent_data[i] for i in range(len(indep_tags))
        }

        return dep_data_dict | indep_data_dict | internal_sweep_dict
