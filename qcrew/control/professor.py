""" The professor is qcrew's experiment run manager. Professor provides the `run_experiment` method, which when called by the user, executes the experiment, enters its fetch-analyze-plot-save loop, and closes the loop by calling the experiment's `update()` method. """

import time

import numpy as np

from qcrew.analyze import stats
from qcrew.control import Stagehand
from qcrew.control.instruments.qm import QMResultFetcher
from qcrew.helpers import logger
from qcrew.measure.experiment import Experiment

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
        plotter = Plotter(experiment)
        db = initialise_database(
            exp_name=EXP_NAME,
            sample_name=SAMPLE_NAME,
            project_name=PROJECT_FOLDER_NAME,
            path=DATAPATH,
            timesubdir=False,
            timefilename=True,
        )

        ##################        LIVE POST-PROCESSING LOOP        ####################

        with DataSaver(db) as datasaver:

            ##############        SAVE MEASUREMENT RUN METADATA       ##################

            datasaver.add_metadata(experiment.parameters)

            while fetcher.is_fetching:

                ###############            FETCH PARTIAL RESULTS         ###############

                partial_results = fetcher.fetch()
                num_results = fetcher.count
                if not partial_results:  # empty dict means no new results available
                    continue

                ################            LIVE SAVE RESULTS         ##################

                datasaver.update_multiple_results(
                    partial_results, save=["I", "Q"], group="data"
                )

                #######            CALCULATE RUNNING MEAN STANDARD ERROR         #######

                zs_raw = np.sqrt(partial_results["Z_SQ_RAW"])
                zs_raw_avg = np.sqrt(partial_results["Z_SQ_RAW_AVG"])
                stderr = stats.get_std_err(zs_raw, zs_raw_avg, num_results, *stderr)

                #############            LIVE PLOT AVAILABLE RESULTS         ###########

                zs = np.sqrt(partial_results["Z_AVG"])  # latest batch of average signal
                xs = partial_results["x"]
                plotter.live_plot(
                    xs, zs, num_results, fit_fn=experiment.fit_fn, err=stderr[0]
                )
                time.sleep(1)  # prevent over-fetching, over-saving, ultra-fast plotting

            ##################         SAVE REMAINING DATA         #####################

            final_save_dict = {"Z_AVG": zs, "x": xs}
            datasaver.add_multiple_results(
                final_save_dict, save=["Z_AVG", "x"], group="data"
            )

        ##########################          fin           #############################

        print(qm_job.execution_report())
