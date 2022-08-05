""" The professor is qcrew's experiment run manager. Professor provides the `run()` method, which when called by the user, executes the experiment, enters its fetch-analyze-plot-save loop, and closes the loop by calling the experiment's `update()` method. """

import time
import numpy as np

from qcrew.analyze import stats
from qcrew.analyze.plotter import Plotter
from qcrew.control import Stagehand
from qcrew.control.instruments.qm import QMResultFetcher
from qcrew.helpers import logger
from qcrew.helpers.datasaver import DataSaver, initialise_database
from qcrew.measure.experiment import Experiment
from qm import SimulationConfig

import matplotlib.pyplot as plt
from IPython import display


def sprint(experiment):
    '''
    First, Get the variables required with Stagehand
    '''
    
    with Stagehand() as stage:
        qm = stage.QM
        config = qm.get_config()

    sim = qm.simulate(
        config,
        experiment,
        SimulationConfig(
            duration=0,
            include_analog_waveforms=False,
            include_digital_waveforms=False,
            simulation_interface=None,
            controller_connections: 
                Optional[List[qm.simulate.interface.ControllerConnection]] = None,
            extraProcessingTimeoutInMs=- 1
        )
    )
    
    '''
    Second, simulate it with qm.simulate(), ensure that all of the
    possible SimulationConfig parameters are considered
    '''
    
    sim = qm.simulate(
        config,
        program,
        SimulationConfig(
            
        )
    )

    '''
    Third, access the results and samples, then plot these however desired
    '''
    
    samples = sim.get_simulated_samples()
    samples.con1.plot()