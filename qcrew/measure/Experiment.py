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
        "reps",  # number of times the experiment is repeated
        "wait_time",  # wait time in nanoseconds between repetitions
    }

    def __init__(
        self,
        reps,
        wait_time,
        x_sweep=None,
        y_sweep=None,
    ):

        # Experiment loop variables
        self.reps = reps
        self.wait_time = wait_time

        # Sweep configurations
        self.sweep_config = {"n": (0, self.reps, 1), "x": x_sweep, "y": y_sweep}
        self.buffering = tuple()  # defined in _configure_sweeps

        # ExpVariable definitions. This list is updated in _configure_sweeps and after
        # stream and variable declaration.
        self.var_list = {
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

        logger.info(f"Created {type(self).__name__}")

    def _configure_sweeps(self, sweep_variables_keys):
        """
        Check if each x and y sweeps are correctly configured. If so, update buffering, variable type, and tag of x and y in var_list accordingly.
        """

        buffering = list()
        for key in sweep_variables_keys:
            # Set its sweep according to user-defined configurations
            if self.sweep_config[key]:
                self.var_list[key].configure_sweep(self.sweep_config[key])

                # Log the type of sweep configured
                if self.var_list[key].sweep_type == "for_":
                    logger.info(f"Configured linear sweep on variable {key}")
                if self.var_list[key].sweep_type == "for_each_":
                    logger.info(
                        f"Configured sweep with arbitrary values on variable {key}"
                    )

                # Update buffering
                buffering.append(self.var_list[key].buffer_len)
                # Flag for buffering in stream processing
                self.var_list[key].buffer = True
                # Define key as memory tag
                self.var_list[key].tag = key

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
        """

        self._configure_sweeps(["x", "y"])

        with qua.program() as qua_sequence:

            # Initial variable and stream declarations
            self.var_list = macros.declare_variables(self.var_list)
            self.var_list = macros.declare_streams(self.var_list)

            # Stores QUA variables as attributes for easy use
            for key, value in self.var_list.items():
                setattr(self, key, value.var)
            # Plays pulse sequence in a loop
            sweep_variables = [self.var_list[key] for key in ["n", "x", "y"]]
            macros.QUA_loop(self.QUA_play_pulse_sequence, sweep_variables)

            # Define stream processing
            buffer_len = np.prod(self.buffering)
            with qua.stream_processing():
                macros.process_streams(self.var_list, buffer_len=buffer_len)
                macros.process_Z_values(
                    self.var_list["I"].stream,
                    self.var_list["Q"].stream,
                    buffer_len=buffer_len,
                )

        return qua_sequence
