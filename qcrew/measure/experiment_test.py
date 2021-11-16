%matplotlib auto

from qcrew.analyze.plotter_test import Plotter
from qcrew.analyze.stats import get_std_err
from qcrew.control.instruments.qm import QMResultFetcher
from qcrew.control import Stagehand
from qcrew.helpers.datasaver import DataSaver, initialise_database
from qcrew.helpers import logger
from qcrew.helpers.parametrizer_test import Parametrized
import qcrew.measure.qua_macros_test as macros

import copy
from qm import qua
import numpy as np
import time
from typing import Optional, Union, List
import abc


class Experiment(Parametrized):
    def __init__(self, parameters: dict, **kwargs):

        # experiment basic
        self.name = parameters.get("name") or self.__class__.__name__
        self.modes = parameters.get("modes")
        self.reps = parameters.get("reps")
        self.wait_time = parameters.get("wait_time") or 100e3  # in nanosecond

        # exp variables
        self.variables = [
            macros.ExpVariable(name="I", var_type=qua.fixed),
            macros.ExpVariable(name="Q", var_type=qua.fixed),
        ]
        self.variables = Experiment.update_variable(
            self.variables, parameters.get("variables")
        )

        # sweep variables
        self.sweep_variables = [
            macros.SweepVariable(name="n", var_type=int, sweep=(0, self.reps, 1)),
        ]
        self.sweep_variables = Experiment.update_variable(
            self.sweep_variables, parameters.get("sweep_variables")
        )

        # stream variables
        self.stream_variables = [
            macros.StreamVariable(name="I_stream"),
            macros.StreamVariable(name="Q_stream"),
        ]
        self.stream_variables = Experiment.update_variable(
            self.stream_variables, parameters.get("stream_variables")
        )

        # data shape
        data_shape_list = [var.length for var in self.sweep_variables]
        self.data_shape = tuple(data_shape_list)

        # buffer shape
        del data_shape_list[0]
        self.buffer_shape = tuple(data_shape_list[::-1]) if data_shape_list else None

        # fetch configurations
        self.fetch_period = 1 or parameters.get("fetch_period")  # in second

        # saving configurations
        self.live_saving_tags = Experiment.update_list(
            [], parameters.get("live_saving_tags")
        )
        self.final_saving_tags = Experiment.update_list(
            [], parameters.get("final_saving_tags")
        )

        # plot variable tags
        self.indep_tags = Experiment.update_list([], parameters.get("indep_tags"))
        self.dep_tags = Experiment.update_list([], parameters.get("dep_tags"))

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
                    "plot_tag": "Z_AVG",
                    "std_tag": ("Z_RAW", "Z_RAW_AVG"),
                }
            ],
        }

        super().__init__(**kwargs)

        # log
        self.stage_modes = self.modes

        logger.info(f"Created {type(self).__name__}")

    def plot_config(self, plot_setup: Optional[dict]) -> None:
        """Update the plotting configurations.

        Args:
            plot_setup (dict): a dictionary contains the updated plotting configurations
        """
        if plot_setup:
            self.plot_setup.update(plot_setup)

    @staticmethod
    def update_list(old: list, new: Optional[list]) -> list:
        if new:
            for item in new:
                if item in old:
                    continue
                else:
                    old.append(item)
        return old

    @staticmethod
    def update_variable(old: list, new: Optional[List[macros.ExpVariable]]) -> list:

        var_name_list = [var.name for var in old]

        if new:
            for new_var in new:
                if new_var.name in var_name_list:
                    index = var_name_list.index(new_var.name)
                    old[index] = new_var
                else:
                    old.append(new_var)
        return old

    @abc.abstractmethod
    def qua_sequence(self, *args, **kwargs):
        pass

    def stream_process(
        self, variables: list, sweep_variables: list, stream_variables: list
    ):

        [I_st, Q_st] = stream_variables

        macros.IQ_results(I_st, Q_st, self.buffer_shape)
        macros.Z_results(I_st, Q_st, self.buffer_shape)

    def qua_program(self):
        # TODO:check the sweep
        with qua.program() as qua_prog:

            # Initial variable
            var = macros.qua_var_declare(self.variables)
            sweep_var = macros.qua_var_declare(self.sweep_variables)
            stream_var = macros.qua_var_declare(self.stream_variables)

            # Loop over sweep variable
            macros.qua_loop(
                qua_function=self.qua_sequence,
                qua_var=var,
                qua_sweep_var=sweep_var,
                qua_stream_var=stream_var,
                sweep_variables=self.sweep_variables,
            )

            with qua.stream_processing():
                self.stream_process(var, sweep_var, stream_var)

        return qua_prog

    def std_tags_list(self) -> list:
        """Get the std tags from the plot setup

        Returns:
            list: Each element is a tuple that consists of the raw data tag, raw avg data tag and avg tag
        """
        std_tags = []
        for item in self.plot_setup["axis"]:
            if item.get("plot_errbar") is True:
                plot_tag = item.get("plot_tag")
                std_tag = item.get("std_tag")
                if plot_tag and std_tag:
                    temp_list = list(std_tag)
                    temp_list.append(plot_tag)
                    std_tags.append(tuple(temp_list))
                    # store the averaged data tag (plot tag) as the third of tuple
                else:
                    raise ValueError(
                        "plot_tag and std_tag are not given in the plot setup."
                    )
        return std_tags

    def create_empty_stderr_data_dict(self) -> dict:
        empty_stderr_data = {}

        for std_tag_tuple in self.std_tags:

            # the third in tuple is avreaged data tag which coincides the plot tag
            std_tag = std_tag_tuple[2]
            empty_stderr_data[std_tag] = (None, None, None)
        return empty_stderr_data

    def estimate_std(
        self, partial_results: dict, num_results: int, stderr_data: dict
    ) -> dict:
        """Estimate the standard deviation dynamically

        Args:
            partial_results (dict): A dictionary contains the partial data fetched from the qm
            num_results (int): The latest repetition number
            stderr_data (dict): A dictionary contains the std calculated by the previous data

        Raises:
            ValueError: [description]

        Returns:
            dict: Update the std
        """
        if len(stderr_data.keys()) == len(self.std_tags):
            new_stderr_data = {}

            for std_tag_tuple in self.std_tags:

                raw_tag = std_tag_tuple[0]
                raw_avg_tag = std_tag_tuple[1]
                avg_tag = std_tag_tuple[2]

                data_raw = partial_results[raw_tag]
                data_avg = partial_results[raw_avg_tag]
                stderr_tuple = get_std_err(
                    data_raw, data_avg, num_results, *stderr_data[avg_tag]
                )
                new_stderr_data[avg_tag] = stderr_tuple

            return new_stderr_data
        else:
            raise ValueError(
                'The number of keys in the argument "stderr_data" dictionary do not match the number in "std_tag".'
            )

    def sqrt_root_data(self, partial_results: dict) -> dict:

        for index, tag in enumerate(self.square_avg_tags):
            new_tag = self.sqrt_avg_tags[index]
            partial_results[new_tag] = np.sqrt(partial_results[tag])

        for index, tag in enumerate(self.square_raw_tags):
            new_tag = self.sqrt_raw_tags[index]
            partial_results[new_tag] = np.sqrt(partial_results[tag])

        for index, tag in enumerate(self.last_square_avg_tags):
            new_tag = self.last_sqrt_avg_tags[index]
            partial_results[new_tag] = np.sqrt(partial_results[tag])

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

    def filter_plot_data(self, partial_results: dict) -> tuple:
        new_dict = self.sqrt_root_data(partial_results)
        dep_data = {}
        indep_data = {}
        for key in self.dep_tags:
            if key in new_dict:
                dep_data[key] = new_dict.get(key)

        for key in self.indep_tags:
            if key in new_dict:
                indep_data[key] = new_dict.get(key)

        return dep_data, indep_data, new_dict

    def plot(
        self,
        plotter: Plotter,
        independent_data: dict,
        dependent_data: dict,
        n: int,
        errbar_dict: dict,
    ) -> None:

        x_tag = self.indep_tags[0]
        y_tag = self.dep_tags[0]
        errbar_tag = self.std_tags[0][2]

        x = independent_data[x_tag]
        y_dict = {y_tag: dependent_data[y_tag]}
        err_dict = {y_tag: errbar_dict[errbar_tag][0]}

        print("=====================")
        print(x_tag, np.shape(x))
        print(y_tag, np.shape(y_dict[y_tag]))
        print(y_dict[y_tag])
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print(np.shape(err_dict[y_tag]))
        print(err_dict[y_tag])
        plotter.live_1dplot(
            plotter.axis[0, 0], x, y_dict, n=n, axis_index=0, errbar_dict=err_dict
        )

    def run(self, group="data", z_calculate: bool = True, z_tag: str = "Z_SQ") -> None:

        # post-calculation
        if z_calculate:
            self.square_raw_tags = [f"{z_tag}_RAW"]
            self.square_avg_tags = [f"{z_tag}_RAW_AVG"]
            self.last_square_avg_tags = [f"{z_tag}_AVG"]

            sqrt_tag = z_tag.replace("_SQ", "")
            self.sqrt_raw_tags = [f"{sqrt_tag}_RAW"]
            self.sqrt_avg_tags = [f"{sqrt_tag}_RAW_AVG"]
            self.last_sqrt_avg_tags = [f"{sqrt_tag}_AVG"]

        self.std_tags = self.std_tags_list()

        with Stagehand() as stage:

            # connect to the stage modes
            for index, mode_name in enumerate(self.modes):
                try:
                    mode = getattr(stage, mode_name)
                except AttributeError:
                    logger.error(f"'{mode_name}' does not exist on stage")
                else:
                    self.stage_modes[index] = mode

            # qua program and result tags
            qua_prog = self.qua_program()

            # execute qm program
            qm_job = stage.QM.execute(qua_prog)

            # initiate fetcher and plotter
            fetcher = QMResultFetcher(handle=qm_job.result_handles)
            plotter = Plotter(self.plot_setup)

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
                stderr_dict = self.create_empty_stderr_data_dict()

                # metadata
                datasaver.add_metadata(self.parameters)
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

                        print("1=============================")
                        print("NUMBER", num_results)
                        print(partial_results.keys())
                        print(np.shape(partial_results["Z_SQ_RAW"]))
                        print(np.shape(partial_results["a"]))

                        dep_data, indep_data, new_data = self.filter_plot_data(
                            partial_results
                        )

                        if self.std_tags:
                            stderr_dict = self.estimate_std(
                                partial_results=new_data,
                                num_results=num_results,
                                stderr_data=stderr_dict,
                            )

                        self.plot(
                            plotter=plotter,
                            independent_data=indep_data,
                            dependent_data=dep_data,
                            n=num_results,
                            errbar_dict=stderr_dict,
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


class PowerRabi(Experiment):
    def __init__(self, parameters):

        param = {
            "name": " Power Rabi",
            "modes": ["RR", "QUBIT"],
            "reps": 1000,
            "wait_time": 1e6,
            "sweep_variables": [
                macros.SweepVariable(
                    name="a", var_type=qua.fixed, sweep=(0.0, 2.0, 0.1)
                )
            ],
            "stream_variables": [
                macros.StreamVariable(name="a_stream"),
            ],
            "dep_tags": ["Z_AVG"],
            "indep_tags": ["a_var"],
            "errbar_tags": ["Z_RAW"],
            "live_saving_tags": ["Z_AVG"],
            "final_saving_tags": ["a"],
        }

        param.update(parameters)

        super().__init__(parameters=param)

    def qua_sequence(
        self, variables: list, sweep_variables: list, stream_variables: list
    ):

        rr, qubit = self.stage_modes
        I, Q = variables
        n, a = sweep_variables
        I_st, Q_st, a_st = stream_variables

        rr.measure((I, Q))
        qua.save(I, I_st)
        qua.save(Q, Q_st)
        qua.save(a, a_st)

    def stream_process(
        self, variables: list, sweep_variables: list, stream_variables: list
    ):

        I_st, Q_st, a_st = stream_variables

        macros.IQ_results(I_st, Q_st, self.buffer_shape)
        macros.Z_results(I_st, Q_st, self.buffer_shape)
        macros.sweep_results(a_st, tag="a_var", buffer_shape=self.buffer_shape)


p = {}
exp = PowerRabi(p)
exp.run()
