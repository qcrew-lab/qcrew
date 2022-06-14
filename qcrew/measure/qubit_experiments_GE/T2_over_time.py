"""
The objective of this experiment is to repeat a T2 measurement
a given number of times after a given period. The frequency is 
saved for each experiment to analyze how it shifts over time.
"""

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.control.instruments.qm import QMResultFetcher

from qcrew.helpers.datasaver import DataSaver, initialise_database

from qcrew.analyze.plotter import Plotter
from qcrew.analyze import stats
from qcrew.analyze import fit

from qcrew.measure.qubit_experiments_GE.T2 import T2

import numpy as np
import time
import datetime

# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    iterations = 72
    exp_idle_time = 10 * 60  # seconds of wait time between experiments

    # list of detuning (in Hz) over time and timestamps
    f0_list = []
    timestamps = []
    # This gives the signal level of the fit, which helps identifying bad T2s
    signal_level = []

    # Initialize database for compiling whole experimental data
    with Stagehand() as stage:

        db = initialise_database(
            exp_name="qubit_spec_current_sweep",
            sample_name=stage.sample_name,
            project_name=stage.project_name,
            path=stage.datapath,
        )

        # Set SQUID current bias
        yoko = stage.YOKO
        yoko.source = "current"
        yoko.level = 0.187e-3
        yoko.state = True

        with DataSaver(db) as datasaver:
            for i in range(iterations):
                ## Do T2 experiment
                x_start = 10
                x_stop = 2000
                x_step = 16
                parameters = {
                    "modes": [stage.QUBIT, stage.RR],
                    "reps": 2000,
                    "wait_time": 400e3,
                    "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
                    "qubit_op": "pi2",
                    "detuning": int(0),
                    "single_shot": False,
                }

                plot_parameters = {
                    "xlabel": "Relaxation time (clock cycles)",
                }

                experiment = T2(**parameters)
                experiment.setup_plot(**plot_parameters)
                plotter = Plotter(experiment.plot_setup)

                # prof.run_with_stage(rr_spec, stage)
                stderr = (None, None, None)
                qua_program = experiment.QUA_sequence()
                qm = stage.QM
                qm_job = qm.execute(qua_program)
                fetcher = QMResultFetcher(handle=qm_job.result_handles)

                while fetcher.is_fetching:
                    # Fetch partial results
                    partial_results = fetcher.fetch()
                    num_results = fetcher.count
                    if not partial_results:
                        # empty dict means no new results available
                        continue

                    # Calculate standard error
                    stderr = experiment.estimate_sd(
                        stats, partial_results, num_results, stderr
                    )

                    # post-process and live plot available results
                    exp_data = experiment.plot_results(
                        plotter, partial_results, num_results, stderr
                    )
                    # prevent over-fetching, over-saving, ultra-fast plotting
                    time.sleep(experiment.fetch_period)

                ## Get frequency of MAXIMUM transmission (transmission measurement)
                zs = np.array(exp_data["Z_AVG"])
                xs = np.array(exp_data["x"])

                # fit and save frequency
                params = fit.do_fit(experiment.fit_fn, xs, zs)
                f0 = params["f0"] / 4e-9  # convert from (clock cycles)**-1 to Hz
                f0_list.append(f0)

                # save timestamp
                timestamp = datetime.datetime.now().strftime("%Y%d%m_%H%M%S")
                timestamps.append(timestamp)

                # save signal level
                amp = params["amp"]
                signal_level.append(amp)

                time.sleep(exp_idle_time)

            data_dict = {
                "detuning": f0_list,
                "timestamps": timestamps,
                "signal_level": signal_level,
            }
            print(data_dict)
            datasaver.add_multiple_results(
                data_dict,
                save=data_dict.keys(),
                group="data",
            )

            yoko = stage.YOKO
            yoko.state = False
