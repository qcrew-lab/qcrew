""" The professor is qcrew's experiment run manager. Professor provides the `run_experiment` method, which when called by the user, executes the experiment, enters its fetch-analyze-plot-save loop, and closes the loop by calling the experiment's `update()` method. """

from qcrew.control import Stagehand
from qcrew.control.stage.stage import Stage
from qcrew.helpers import logger
from qcrew.measure.Experiment import Experiment
from qm.QmJob import QmJob


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

        fetcher = Fetcher(handle=qm_job.result_handles, num_results=experiment.reps)
        plotter = Plotter(experiment)
        stats = (None, None, None)  # to hold running (stderr, mean, variance * (n-1))

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

            datasaver.add_metadata(exp_params)

            while fetcher.is_fetching:
                ###############            FETCH PARTIAL RESULTS         ###############

                (num_so_far, update_results) = fetcher.fetch()
                if (
                    not update_results
                ):  # empty dict return means no new results are available
                    continue
                ################            LIVE SAVE RESULTS         ##################
                datasaver.update_multiple_results(
                    update_results, save=["I", "Q"], group="data"
                )

                #######            CALCULATE RUNNING MEAN STANDARD ERROR         #######

                zs_raw = np.sqrt(update_results["Z_SQ_RAW"])
                zs_raw_avg = np.sqrt(update_results["Z_SQ_RAW_AVG"])
                stats = get_std_err(zs_raw, zs_raw_avg, num_so_far, *stats)

                #############            LIVE PLOT AVAILABLE RESULTS         ###########

                zs = np.sqrt(update_results["Z_AVG"])  # latest batch of average signal
                xs = update_results["x"]
                plotter.live_plot(
                    xs, zs, num_so_far, fit_fn=experiment.fit_fn, err=stats[0]
                )
                time.sleep(1)  # prevent over-fetching, over-saving, ulta-fast live plotting

            ##################         SAVE REMAINING DATA         #####################

            # to save final average and sweep variables, we extract them from "update_results"
            final_save_dict = {"Z_AVG": zs, "x": xs}
            datasaver.add_multiple_results(
                final_save_dict, save=["Z_AVG", "x"], group="data"
            )

        ##########################          fin           #############################

        # TODO experiment.update()
        print(qm_job.execution_report())
