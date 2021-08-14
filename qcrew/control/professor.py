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


def temp_live_plot(x, y, n, err, fit_fn=None):
    plt.cla()
    plt.errorbar(
        x,
        y,
        yerr=err,
        ls="none",
        lw=1,
        ecolor="black",
        marker="o",
        ms=4,
        mfc="black",
        mec="black",
        capsize=3,
        fillstyle="none",
    )
    plt.title(f"{n} reps")
    display.display(plt.gcf())  # plot latest batch
    display.clear_output(wait=True)  # clear plot when new plot is available


def run(experiment: Experiment) -> None:
    """ """

    ##########################        CONNECT TO STAGE        ##########################

    with Stagehand() as stage:

        ###################        LINK EXPERIMENT AND MODES        ####################

        for index, mode_name in enumerate(experiment.modes):
            try:
                mode = getattr(stage, mode_name)
            except AttributeError:
                logger.error(f"'{mode_name}' does not exist on stage")
                raise
            else:
                experiment.modes[index] = mode

        #########################        RUN EXPERIMENT        #########################

        qua_program = experiment.QUA_sequence()
        qm_job = stage.QM.execute(qua_program)

        #########################        INVOKE HELPERS        #########################

        fetcher = QMResultFetcher(handle=qm_job.result_handles)
        stderr = (None, None, None)  # to hold running (stderr, mean, variance * (n-1))

        plotter = Plotter(experiment.plot_setup)

        db = initialise_database(
            exp_name=experiment.name,
            sample_name=stage.sample_name,
            project_name=stage.project_name,
            path=stage.datapath,
        )

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

                stderr = experiment.estimate_sd(
                    stats, partial_results, num_results, stderr
                )

                #############            LIVE PLOT AVAILABLE RESULTS         ###########

                final_save_dict = experiment.plot_results(
                    plotter, partial_results, num_results, stderr
                )
                time.sleep(1)  # prevent over-fetching, over-saving, ultra-fast plotting

            ##################         SAVE REMAINING DATA         #####################

            datasaver.add_multiple_results(
                final_save_dict, save=final_save_dict.keys(), group="data"
            )

        ##########################          fin           #############################

        print(qm_job.execution_report())
