""" The professor is qcrew's experiment run manager. Professor provides the `run_experiment` method, which when called by the user, executes the experiment, enters its fetch-analyze-plot-save loop, and closes the loop by calling the experiment's `update()` method. """

from qcrew.control.stage.stage import Stage
from qcrew.measure.Experiment import Experiment


class Professor:
    """ """

    def __init__(self, experiment: Experiment, stage: Stage) -> None:
        self.experiment = experiment
        self.stage = stage

    def run(self) -> None:
        
