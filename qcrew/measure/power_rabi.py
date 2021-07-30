"""
A python class describing a power rabi measurement using the QM 
system. 
This class serves as a QUA script generator with user-defined parameters. It 
also defines how the information is retrieved from result handles.
"""
# --------------------------------- Imports ------------------------------------
from qm import qua

from qcrew.helpers.parametrizer import Parametrized
from typing import ClassVar
from qcrew.measure.Experiment import Experiment
from qcrew.control import Stagehand
import qua_macros as macros

# ---------------------------------- Class -------------------------------------


class PowerRabi(Experiment):

    _parameters: ClassVar[set[str]] = Experiment._parameters | {
        "mode_names",  # names of the modes used in the experiment
        "qubit_op",  # operation used for exciting the qubit
        "fit_fn",  # Fit function
    }

    def __init__(self, modes, qubit_op, fit_fn="sine", **other_params):

        self.mode_names = modes  # mode names for saving metadata
        self.modes = None  # is updated with mode objects by the professor
        self.qubit_op = qubit_op
        self.fit_fn = fit_fn

        super().__init__(**other_params)  # Passes other parameters to parent

    def QUA_play_pulse_sequence(self):
        """
        Defines pulse sequence to be played inside the experiment loop
        """
        qubit, rr = self.modes  # get the modes

        qubit.play(self.qubit_op, ampx=self.x)  # play qubit pulse
        qua.align(qubit.name, rr.name)  # wait qubit pulse to end
        rr.measure((self.I, self.Q))  # measure qubit state
        qua.wait(int(self.wait_time // 4), qubit.name)  # wait system reset

        macros.stream_results(self.var_list)  # stream variables (I, Q, x, etc)


# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    parameters = {
        "modes": ("QUBIT", "RR"),
        "reps": 200000,
        "wait_time": 32000,
        "x_sweep": (-1.9, 1.9 + 0.2 / 2, 0.2),
        # "y_sweep": [True, False],
        "qubit_op": "gaussian_pulse",
    }

    experiment = PowerRabi(**parameters)

    # The following will be done by the professor
    with Stagehand() as stage:

        mode_tuple = tuple()
        for mode_name in experiment.mode_names:
            mode_tuple += (getattr(stage, mode_name),)

        experiment.modes = mode_tuple

        power_rabi = experiment.QUA_sequence()

        ###################        RUN MEASUREMENT        ############################

        job = stage.QM.execute(power_rabi)

    """
    ####################        INVOKE HELPERS        ###########################
    # fetch helper and plot hepler

    fetcher = Fetcher(handle=job.result_handles, num_results=experiment.reps)
    plotter = Plotter(title=EXP_NAME, xlabel="Amplitude scale factor")
    stats = (None, None, None)  # to hold running stats (stderr, mean, variance * (n-1))

    # initialise database under dedicated folder
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

        ###############        SAVE MEASUREMENT RUN METADATA       ###################

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

            ########            CALCULATE RUNNING MEAN STANDARD ERROR         #########

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

    print(job.execution_report())
    """
