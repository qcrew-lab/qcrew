
from qcrew.analyze.plotter import Plotter
from qcrew.analyze.stats import get_std_err
from qcrew.control.instruments.qm import QMResultFetcher
from qcrew.control import Stagehand
from qcrew.helpers.datasaver import DataSaver, initialise_database
from qcrew.helpers import logger
from qcrew.helpers.parametrizer_test import Parametrized
import qcrew.measure.qua_macros_test as macros

from qm import qua
import numpy as np
import time
from typing import Optional, Union, List
import abc

class Experiment(Parametrized):

    def __init__(self, parameters: dict, **kwargs):
        # experiment basic 
        self.name = self.__class__.__name__ or parameters.get("name")
        self.modes = parameters.get("modes")
        self.reps = parameters.get("reps")
        self.wait_time = 100e3 or parameters.get("wait_time") # in nanosecond
        
        # exp variables 
        self.variables = [
            macros.ExpVariable(name="I", var_type=qua.fixed),
            macros.ExpVariable(name="Q", var_type=qua.fixed)
        ]
        self.update_variable(parameters.get("variables"))
        
        # sweep variables
        self.sweep_variables= [
            macros.SweepVariable(name="n", var_type=int, sweep=(0, self.reps, 1)),
        ]
        self.update_sweep_variable(parameters.get("sweep_variables"))

        # stream variables 
        self.stream_variables = [
            macros.StreamVariable(name="I_stream"),
            macros.StreamVariable(name="Q_stream")
        ]
        self.update_stream_variable(parameters.get("stream_variables"))

        # data shape
        data_shape_list = []
        for var in self.sweep_variables:
            data_shape_list.append(var.length)
        self.data_shape = tuple(data_shape_list)

        # buffer shape
        del data_shape_list[0]
        self.buffer_shape = tuple(data_shape_list.reverse())

        
        # qua plotting variables 
        self.indep_tags = []
        self.dep_tags = []
        self.indep_tags.extend(parameters.get("indep_tags"))
        self.dep_tags.extend(parameters.get("dep_tags"))

        # fetch configurations
        self.fetch_period = 1 or parameters.get("fetch_period") # in second
        
        # saving configurations
        self.live_saving_tags = [self.variables[0].name, self.variables[1].name]
        self.final_saving_tags = []
        self.parameter_saving_tags = self.indep_tags

        self.live_saving_tags.extend(parameters.get("live_saving_tags"))
        self.final_saving_tags.extend(parameters.get("final_saving_tags"))
        self.parameter_saving_tags.extend(parameters.get("parameter_saving_tags"))

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

        # initization the parent class 
        super().__init__(**kwargs)


        # log
        logger.info(f"Created {type(self).__name__}")

    def plot_config(self, plot_setup: Optional[dict]) -> None:
        """Update the plotting configurations.

        Args:
            plot_setup (dict): a dictionary contains the updated plotting configurations
        """
        self.plot_setup.update(plot_setup)
    
    def update_variable(self, variable: Optional[List[macros.ExpVariable]]) -> None:
        var_name_list = [var.name for var in self.variables]
        
        if variable:
            for new_var in variable:
                if new_var.name in var_name_list:
                    index = var_name_list.index(new_var.name)
                    self.variables[index] = new_var
                else:
                    self.variables.append(new_var)
    
    def update_sweep_variable(self, variable: Optional[List[macros.ExpVariable]]) -> None:
        var_name_list = [var.name for var in self.sweep_variables]
        
        if variable:
            for new_var in variable:
                if new_var.name in var_name_list:
                    index = var_name_list.index(new_var.name)
                    self.sweep_variables[index] = new_var
                else:
                    self.sweep_variables.append(new_var)
    
    def update_stream_variable(self, variable: Optional[List[macros.ExpVariable]]) -> None:
        var_name_list = [var.name for var in self.stream_variables]
        
        if variable:
            for new_var in variable:
                if new_var.name in var_name_list:
                    index = var_name_list.index(new_var.name)
                    self.stream_variables[index] = new_var
                else:
                    self.stream_variables.append(new_var)
    
    @abc.abstractmethod
    def qua_sequence(self):
        pass
    
    @abc.abstractmethod
    def stream_process(self, 
                       variables:list,
                       sweep_variables:list,
                       stream_variables:list):
        i_st = stream_variables[0]
        q_st = stream_variables[1]
        
        result_tag = []
        res_iq = macros.IQ_results(i_st, q_st, self.buffer_shape)
        res_z = macros.Z_results(i_st, q_st, self.buffer_shape)
        
        result_tag.extend(res_iq)
        result_tag.extend(res_z)

        return result_tag

    def qua_program(self):

        # TODO:check the sweep
        with qua.program() as qua_prog:

            # Initial variable 
            var = macros.qua_var_declare(self.variables)
            sweep_var = macros.qua_var_declare(self.sweep_variables)
            stream_var = macros.qua_var_declare(self.stream_variables)

            macros.qua_loop(self.qua_sequence, 
                            sweep_variables=self.sweep_variables, 
                            declared_variables=sweep_var)
            
            
            with qua.stream_processing():
                result_tag = macros.stream_process(variables=var,
                                                    sweep_variables=sweep_var,
                                                    stream_variables=stream_var)

        return result_tag, qua_prog

    def create_empty_stderr_data_dict(self) -> dict:

        empty_stderr_data = {}
        for std_tag_pair in self.std_tags:
            raw_tag = std_tag_pair[0]
            empty_stderr_data[raw_tag] = (None, None, None)
        return empty_stderr_data

    def estimate_std(self, partial_results: dict, num_results: int, stderr_data: dict) -> dict:
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

    def std_tags_list(self) -> list:
        
        std_tags = []
        for item in self.plot_setup["axis"]:
            if item.get("plot_errbar") == True:
                std_tags.append(item.get("std_tag"))

        return std_tags

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
    
    def filter_plot_data(self, partial_results:dict, stderr_data: dict) -> None:
        new_dict = self.sqrt_root_data(partial_results)
        dep_data = {}
        indep_data = {}
        for key in self.dep_tags:
            if key in new_dict:
                dep_data[key] = new_dict.get(key)
        
        for key in self.indep_tags:
            if key in new_dict:
                indep_data[key] = new_dict.get(key)

        return dep_data, indep_data, stderr_data

    def plot(self,
        plotter: Plotter,
        independent_data: dict,
        dependent_data: dict,
        n: int,
        errbar_dict: dict) -> None:

        x_tag = self.indep_tags[0]
        y_tag = self.dep_tags[0]

        x = independent_data[x_tag]
        y_dict = {y_tag: dependent_data[y_tag]}
        err_dict = {y_tag: errbar_dict[y_tag]}

        plotter.live_1dplot(plotter.axis[0, 0], x, y_dict, n=n, axis_index=0, errbar_dict=err_dict) 

    def run(self, 
            group="data", 
            z_calculate:bool=True, 
            z_tag:str="Z_SQ") -> None:

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
            result_tag, qua_program = self.qua_program()
            
            # execute qm program
            qm_job = stage.QM.execute(qua_program)

            # initiate fetcher and plotter
            fetcher = QMResultFetcher(handle=qm_job.result_handles)
            plotter = Plotter(self.plot_setup)
            
            # initialize the database
            db = initialise_database(exp_name=self.name,
                                        sample_name=stage.sample_name,
                                        project_name=stage.project_name,
                                        path=stage.datapath)

            # datasaver manager
            with DataSaver(db) as datasaver:
                
                # std error
                stderr_dict = self.create_empty_stderr_data_dict

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

                        if self.std_tags:
                            stderr_dict = self.estimate_std(
                                partial_results=partial_results,
                                num_results=num_results,
                                stderr_data=stderr_dict,
                            )

                        dep_data, indep_data, error_data = self.filter_plot_data(
                            partial_results=partial_results, stderr_data=stderr_dict
                        )
                        self.plot(
                            plotter=plotter,
                            independent_data=indep_data,
                            dependent_data=dep_data,
                            n=num_results,
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


class PowerRabi(Experiment):
    def __init__(self, parameters):

        a_start = parameters.get("a_start")
        a_stop = parameters.get("a_stop")
        a_step = parameters.get("a_step")

        param = {
            "name": "Power Rabi",
            "modes": ["RR", "QUBIT"],
            "reps": 100,
            "wait_time":1e6, 
            "sweep_variables":[
                macros.SweepVariable(name="a", var_type=int, sweep=(a_start, a_stop, a_step))
                ],
        }
        param.update(parameters)

        super().__init__(param)


param = {
    "name": "Power Rabi",
    "reps": 100,
    "wait_time":1e6, 
    "a_start":-2,
    "a_stop": 2,
    "a_step": 0.05,
}

exp = PowerRabi()

        




        
