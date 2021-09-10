from qcrew.helpers import logger
from qcrew.analyze.plotter import Plotter
from qcrew.analyze.stats import get_std_err
from qcrew.control.instruments.qm import QMResultFetcher
import qcrew.measure.qua_macros as macros
from qcrew.control import Stagehand
from qcrew.analyze.plotter import Plotter
from qcrew.helpers.datasaver import DataSaver, initialise_database
from qm import qua
import numpy as np
import time
from typing import Optional, Union, List
import abc

class Experiment:
    def __init__(self, param: dict):
        self._parameters = param

        # experiment name
        self.name = self.__class__.__name__ or param.get("name")

        # modes
        self.modes = []
        self._mode_names = param.get("mode")

        # qua program parameters
        self.indep_tags = set()
        self.dep_tags = set()
        self.reps = 100 or param.get("reps")  # number of repetition
        self.wait_time = 100e3 or param.get(
            "wait_time"
        )  # wait time in nanoseconds between repetitions
        # TODO: check the sign
        self.buffer_list = [len(np.arrange(0, self.reps + 1 / 2, 1))]
        if "sweep" in param:
            for sweep_tuple in param.get("sweep"):
                self.sweep_config = [("n", 0, self.reps, 1)].append(sweep_tuple)
                self.indep_tags.update(sweep_tuple[0])

                if len(sweep_tuple) == 4:
                    length = len(
                        np.arrange(
                            sweep_tuple[1],
                            sweep_tuple[2] + sweep_tuple[3] / 2,
                            sweep_tuple[3],
                        )
                    )
                elif len(sweep_tuple) == 2:
                    if isinstance(sweep_tuple[1], list):
                        length = len(sweep_tuple[1])
                    elif isinstance(sweep_tuple[1], np.ndarray):
                        length = sweep_tuple[1].size
                self.buffer_list.append(length)
        self.buffer = tuple(self.buffer_list)

        self.variables = {
            "n": macros.ExpVariable(var_type=int, sweep=self.sweep_config["n"]),
            "x": macros.ExpVariable(average=False, save_all=False),
            "y": macros.ExpVariable(average=False, save_all=False),
            "I": macros.ExpVariable(tag="I", var_type=qua.fixed, buffer=True),
            "Q": macros.ExpVariable(tag="Q", var_type=qua.fixed, buffer=True),
        }

        # fetch configurations
        self.fetch_period = 1 or param.get(
            "fetch_period"
        )  # wait time between fetching and plotting

        # post-calculation parameters
        self.square_avg_tags = ["Z_SQ_RAW_AVG"].append(param.get("square_avg_tags"))
        self.square_raw_tags = ["Z_SQ_RAW"].append(param.get("square_raw_tags"))
        self.sqrt_raw_avg_tags = ["Z_RAW_AVG"].append(param.get("sqrt_avg_tags"))
        self.sqrt_raw_tags = ["Z_RAW"].append(param.get("sqrt_raw_tags"))
        self.sqrt_avg_tags = ["Z_AVG"].append(param.get("sqrt_tags"))

        # saving configurations
        self.live_saving_tags = set([self.variables["I"].tag, self.variables["Q"].tag])
        self.final_saving_tags = set(self.sqrt_avg_tags)
        self.parameter_saving_tags = self.indep_tags

        # plot configurations
        self.plot_setup = {
            "suptitle": None,
            "nrow": 1,
            "ncol": 1,
            "axis": [
                {
                    "title": self.name,
                    "plot_type": "scatter",
                    "plot_errbar": True,
                    "xlabel": None,
                    "ylabel": "Signal (a.u.)",
                    "trace_label": None,
                }
            ],
            "plot_tags": ["Z_AVG"],
        }
        self.plot_config(plot_setup=None)

        # log
        logger.info(f"Created {type(self).__name__}")

    @property
    def modes(self):
        return self._mode_names

    @property
    def parameters(self):
        return self._parameters

    def update_variable(self, variable: dict[str, macros.ExpVariable]) -> None:
        self.variables.update(variable)

    def plot_config(self, plot_setup: Optional[dict]) -> None:
        """Update the plotting configurations.

        Args:
            plot_setup (dict): a dictionary contains the updated plotting configurations
        """
        self.plot_setup.update(plot_setup)
        self.plot_tags = self.plot_setup.get("plot_tags")
    
    @abc.abstractmethod
    def qua_sequence(self):
        pass

    def qua_program(self):
        # check the sweep
        
        with qua.program() as qua_prog:

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

        return qua_prog
    
    def qua_stream_results(self):
        """
        Execute stream_results macro in macros library. Meant to be used in
        self.QUA_play_pulse_sequence.
        """
        macros.stream_results(self.variables)

    def create_empty_stderr_data(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        empty_stderr_data = {}
        for std_tag_pair in self.std_tags:
            raw_tag = std_tag_pair[0]
            empty_stderr_data[raw_tag] = (None, None, None)
        return empty_stderr_data

    def estimate_std(
        self, partial_results: dict, num_results: int, stderr_data: dict
    ) -> dict:
        """[summary]

        Args:
            partial_results (dict): [description]
            num_results (int): [description]
            stderr (np.ndarray): [description]

        Returns:
            stderr_tuple (tuple): [description]
        """
        if len(stderr_data.keys()) == len(self.std_tags):
            new_stderr_data = {}

            for std_tag_pair in self.std_tags:
                raw_tag = std_tag_pair[0]
                avg_tag = std_tag_pair[1]
                data_raw = partial_results[raw_tag]
                data_avg = partial_results[avg_tag]
                stderr_tuple = get_std_err(
                    data_raw, data_avg, num_results, *stderr_data[raw_tag]
                )
                new_stderr_data[raw_tag] = stderr_tuple

            return new_stderr_data
        else:
            raise ValueError(
                'The number of keys in the argument "stderr_data" dictionary do not match the number in "std_tag".'
            )

    def sqrt_root_data(self, partial_results: dict) -> dict:

        for index, tag in enumerate(self.square_avg_tags):
            new_tag = self.sqrt_avg_tags[index]
            partial_results[new_tag] = np.sqrt(partial_results[tag]).reshape(
                self.buffer
            )

        for index, tag in enumerate(self.square_raw_tags):
            new_tag = self.sqrt_raw_tags[index]
            partial_results[new_tag] = np.sqrt(partial_results[tag]).reshape(
                self.buffer
            )

        return partial_results

    def get_plot_data(self, partial_results: dict, stderr: Optional[tuple]):

        dep_data = {}
        indep_data = {}

        for tag in self.dep_tags:
            if tag in partial_results and tag in self.square_avg_tags:
                root = np.sqrt(partial_results[tag]).reshape(self.buffer)
                dep_data[tag] = root

            elif tag in partial_results:
                dep_data[tag] = partial_results[tag]

        for tag in self.indep_tags:
            if tag in partial_results:
                indep_data[tag] = partial_results[tag]

        if stderr:
            error_data = stderr[0].reshape(self.buffer)
        else:
            error_data = None

        return dep_data, indep_data, error_data

    def plot(
        self,
        plotter: Plotter,
        independent_data: dict,
        dependent_data: dict,
        n: int,
        fit_func: str,
        errbar: tuple,
    ):

        plotter.live_1dplot(
            plotter.axis[0, 0], independent_data, dependent_data, n, fit_func, errbar
        )

    def run(self, group="data") -> None:

        with Stagehand() as stage:

            # connect to the modes of the stage
            for index, mode_name in enumerate(self._mode_names):
                try:
                    mode = getattr(stage, mode_name)
                except AttributeError:
                    logger.error(f"'{mode_name}' does not exist on stage")
                else:
                    self.modes[index] = mode

            # get the qua program
            qua_program = self.qua_program()

            qm_job = stage.QM.execute(qua_program)
            fetcher = QMResultFetcher(handle=qm_job.result_handles)
            self.plotter = Plotter(self.plot_setup.plot_setup)
            # initialize the database
            db = initialise_database(
                exp_name=self.name,
                sample_name=stage.sample_name,
                project_name=stage.project_name,
                path=stage.datapath,
            )

            # datasaver manager
            with DataSaver(db) as datasaver:

                # std error
                stderr = (None, None, None)

                # metadata
                datasaver.add_metadata(self._parameters)
                for mode in stage.modes:
                    datasaver.add_metadata(mode.parameters)

                # fetch data
                while fetcher.is_fetching:

                    partial_results = fetcher.fetch()
                    num_results = fetcher.count

                    if partial_results:  # empty dict means no new results available

                        datasaver.update_multiple_results(
                            partial_results, save=self.live_saving_tags, group=group
                        )

                        stderr = self.estimate_std(
                            partial_results=partial_results,
                            num_results=num_results,
                            stderr=stderr,
                        )

                        dep_data, indep_data, error_data = self.filter_plot_data(
                            partial_results=partial_results, stderr=stderr
                        )
                        self.plot(
                            plotter=self.plotter,
                            independent_data=indep_data,
                            dependent_data=dep_data,
                            n=num_results,
                            fit_func=self.fit_func,
                            errbar=error_data,
                        )
                        time.sleep(1)
                    else:
                        time.sleep(1)
                        continue

                final_save_dict = fetcher.fetch()
                datasaver.add_multiple_results(
                    final_save_dict, save=self.final_saving_tags, group=group
                )

        qm_job.execution_report()


class RRSpectroscopy(Experiment):
    def __init__(self, parameters):
        super().__init__(parameters)

    def QUA_play_pulse_sequence(self):

        (rr,) = self.modes  # get the modes

        qua.update_frequency(rr.name, self.x)  # update resonator pulse frequency
        rr.measure((self.I, self.Q))  # , ampx=self.y)  # measure transmitted signal
        qua.wait(int(self.wait_time // 4), rr.name)  # wait system reset

        self.QUA_stream_results()  # stream variables (I, Q, x, etc)

    def plot(
        self, plotter, independent_data, dependent_data, n, fit_func, errbar, **kwargs
    ):
        plotter.live_1dplot(
            plotter.axis[0, 0],
            independent_data,
            dependent_data,
            n,
            "lorentzian",
            errbar,
        )
