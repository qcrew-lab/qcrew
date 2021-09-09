from qcrew.helpers import logger
from qcrew.analyze.plotter import Plotter
import qcrew.measure.qua_macros as macros
from qm import qua
import numpy as np

class Experiment():
    def __init__(self, param:dict):
        self._parameters = param
        self.fetch_tags = set()
        self.live_saving_tags = set()
        self.final_saving_tags = set()
        self.std_tags = set()
        self.plot_tags =set()
        self.indep_tags = set()
        self.dep_tags = set()
        self.sqrt_tags = set()
        
        #TODO
        # parameters
        self.exp_name = ""
        
        # sweep configurations
        self.sweep_config = {}
        self.buffer = tuple()

        # stream and variable declaration.
        self.variables = {
            "I": macros.ExpVariable(tag="I", var_type=qua.fixed, buffer=True),
            "Q": macros.ExpVariable(tag="Q", var_type=qua.fixed, buffer=True),
            "res": macros.ExpVariable(tag="res", var_type=bool, buffer=True),
        }
   
        # plot configurations
        self.plot_setup = {
            "suptitle": None,
            "nrow": 1,
            "ncol": 1,
            "axis": [{"title":self.exp_name,
                      "plot_type": "scatter",
                      "plot_err": True,
                      "xlabel": None,
                      "ylabel": "Signal (a.u.)",
                      "trace_label": None
                      }]
            
        }
        
        # log
        logger.info(f"Created {type(self).__name__}")
        
    @property
    def parameters(self):
        return self._parameters
    
    def plot_config(self, plot_setup:dict):
        """Update the plotting configurations.

        Args:
            plot_setup (dict): a dictionary contains the updated plotting configurations
        """
        self.plot_setup.update(plot_setup)
        
    def QUA_program(self):
        pass
    
    def estimate_sd(self,
                    statistician,
                    partial_results,
                    num_results,
                    stderr):
        """
        Method to call the statistician and estimate running mean standard error.
        stderr holds the running values of (stderr, mean, variance * (n-1))
        """

        # TODO do this for multiple dependent variables

        zs_raw = np.sqrt(partial_results[self.Z_SQ_RAW_tag])
        zs_raw_avg = np.sqrt(partial_results[self.Z_SQ_RAW_AVG_tag])
        stderr = statistician.get_std_err(zs_raw, zs_raw_avg, num_results, *stderr)

        return stderr
    
    def filter_plot_data(self,
                         partial_results: dict,
                         stderr:np.ndarray):
        
        dep_data = {}
        indep_data = {}
        for tag in self.dep_tags:
            if tag in partial_results and tag in self.sqrt_tags:
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
                
                
                
        

    def plot(self,
             plotter: Plotter,
             independent_data: dict,
             dependent_data: dict,
             n: int,
             fit_func: str,
             errbar:np.ndarray):
   
        plotter.live_1dplot(plotter.axis[0, 0], independent_data, dependent_data,n, fit_func, errbar)

    
    def run(self):
        pass
        
 