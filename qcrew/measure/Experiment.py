# general packages
from qcrew.helpers.parametrizer import Parametrized
from qcrew.helpers import logger
from typing import ClassVar
import numpy as np
import qua_macros as macros
import abc

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
    }

    def __init__(
        self,
        modes,
        reps,
        wait_time,
        x_sweep=None,
        y_sweep=None,
    ):

        # List of modes used in the experiment. String values will be replaced by
        # corresponding modes by the professor module.
        self.modes = modes

        # Experiment loop variables
        self.reps = reps
        self.wait_time = wait_time

        # Sweep configurations
        self.sweep_config = {"n": (0, self.reps, 1), "x": x_sweep, "y": y_sweep}
        self.buffering = tuple()  # defined in _configure_sweeps

        # ExpVariable definitions. This list is updated in _configure_sweeps and after
        # stream and variable declaration.
        self.variables = {
            "n": macros.ExpVariable(var_type=int, sweep=self.sweep_config["n"]),
            "x": macros.ExpVariable(average=False, save_all=False),
            "y": macros.ExpVariable(average=False, save_all=False),
            "I": macros.ExpVariable(tag="I", var_type=qua.fixed, buffer=True),
            "Q": macros.ExpVariable(tag="Q", var_type=qua.fixed, buffer=True),
        }

        # Extra memory tags for saving server-side stream operation results
        self.Z_SQ_RAW_tag = "Z_SQ_RAW"
        self.Z_SQ_RAW_AVG_tag = "Z_SQ_RAW_AVG"
        self.Z_AVG_tag = "Z_AVG"

        # return the tags of the data to be used in the standard deviation estimation
        self.sd_estimation_tags = [self.Z_SQ_RAW_tag, self.Z_SQ_RAW_AVG_tag]

        # return the tags of the data to be used in live saving
        self.live_saving_tags = [self.variables["I"].tag, self.variables["Q"].tag]

        # parameters to be used by the plotter. Updated in self.setup_plot method.
        self.plot_setup = dict()
        self.setup_plot(**self.plot_setup)

        logger.info(f"Created {type(self).__name__}")

    @property
    def mode_names(self):
        # return the name of each mode object in self.modes
        # Assumes the professor has already updated self.modes
        return [mode.name for mode in self.modes]

    @property
    def results_tags(self):
        # return the tags for independent variables x, y (if applicable) and dependent
        # variable z for live plotting and data saving.
        tags = [self.Z_AVG_tag]
        for var in ["x", "y"]:
            if self.variables[var].tag:
                tags.append(self.variables[var].tag)

        return tags

    def setup_plot(
        self,
        xlabel=None,
        ylabel=None,
        zlabel="Signal (a.u.)",
        legend=[],
        title=None,
        plot_type="1D",
    ):
        """
        Updates self.plot_setup dictionary with the parameters to be used by the
        plotter.

        The x and y labels are set up independently if the corresponding sweep exists.

        plot_type identifies how the plotter should arrange the data. If "1D" and x,y
        sweeps are configured, one x sweep trace is plotted for every value of y. If
        the user wants to plot a colormesh instead, pass plot_type = '2D'.

        legend is a list of labels for each trace. If plot_type = "1D" and a y sweep is
        configured, each label will correspond to a value of y.

        """

        self.plot_setup = {
            "xlabel": xlabel,
            "ylabel": ylabel,
            "zlabel": zlabel,
            "legend": legend,
            "title": title,
            "plot_type": plot_type,
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

        self.buffering = tuple(buffering)

        if len(self.buffering) == 0:
            logger.warning("No sweep is configured")
        return

    @abc.abstractmethod
    def QUA_play_pulse_sequence(self):
        """
        Macro that defines the QUA pulse sequence inside the experiment loop. It is
        specified by the experiment (spectroscopy, power rabi, etc.) in the child class.
        """
        pass

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
            sweep_variables = [self.variables[key] for key in ["n", "y", "x"]]
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
