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

import matplotlib.pyplot as plt
from IPython import display


def run_with_stage(experiment, stage):
    """use this method if you don't want the professor to open the stage through the stagehand, but you need to pass in the stage to this method (which you should open in your experiment class __name__ == "__main__" block)"""

    qua_program = experiment.QUA_sequence()
    qm = stage.QM
    qm_job = qm.execute(qua_program)

    #########################        INVOKE HELPERS        #########################

    fetcher = QMResultFetcher(handle=qm_job.result_handles)
    stderr = (None, None, None)  # to hold running (stderr, mean, variance * (n-1))

    db = initialise_database(
        exp_name=experiment.name,
        sample_name=stage.sample_name,
        project_name=stage.project_name,
        path=stage.datapath,
    )  # db.filename

    # Update experiment with the filename of the data
    # Filename will be sent to the plotter as title if no other title is set.
    experiment.filename = db.filename

    plotter = Plotter(experiment.plot_setup)

    ##################        LIVE POST-PROCESSING LOOP        ####################

    with DataSaver(db) as datasaver:

        ##############        SAVE MEASUREMENT RUN METADATA       ##################

        datasaver.add_metadata(experiment.parameters)
        for mode in stage.modes:
            datasaver.add_metadata(mode.parameters)

        while fetcher.is_fetching:

            ###############            FETCH PARTIAL RESULTS         ###############

            partial_results = fetcher.fetch()
            num_results = fetcher.count
            if not partial_results:  # empty dict means no new results available
                continue

            ################            LIVE SAVE RESULTS         ##################

            datasaver.update_multiple_results(
                partial_results, save=experiment.live_saving_tags, group="data"
            )

            #######            CALCULATE RUNNING MEAN STANDARD ERROR         #######

            if experiment.plot_setup["plot_err"] == True:
                stderr = experiment.estimate_sd(
                    stats, partial_results, num_results, stderr
                )
            else:
                stderr = ([],)

            #############            LIVE PLOT AVAILABLE RESULTS         ###########

            data_dict = experiment.plot_results(
                plotter, partial_results, num_results, stderr
            )
            time.sleep(
                experiment.fetch_period
            )  # prevent over-fetching, over-saving, ultra-fast plotting

        ##################         SAVE REMAINING DATA         #####################

        datasaver.add_multiple_results(data_dict, save=data_dict.keys(), group="data")

    ##########################          fin           #############################

    print(qm_job.execution_report())


def run(experiment: Experiment) -> None:
    """ """

    ##########################        CONNECT TO STAGE        ##########################

    with Stagehand() as stage:

        ###################        LINK EXPERIMENT AND MODES        ####################
        print(experiment.modes)
        for index, mode_name in enumerate(experiment.modes):
            if type(mode_name) is str:
                try:
                    mode = getattr(stage, mode_name)
                except AttributeError:
                    logger.error(f"'{mode_name}' does not exist on stage")
                    raise
                else:
                    experiment.modes[index] = mode

        #########################        RUN EXPERIMENT        #########################

        run_with_stage(experiment, stage)
