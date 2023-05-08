"""
A python class describing a qubit spectroscopy using QM for different values of
current in a current source.
This class serves as a QUA script generator with user-defined parameters.
"""

from qcrew.control import professor as prof
from qcrew.control import Stagehand
from qcrew.control.instruments.qm import QMResultFetcher

from qcrew.helpers.datasaver import DataSaver, initialise_database

from qcrew.analyze.plotter import Plotter
from qcrew.analyze import stats

from qcrew.measure.qubit_experiments_GE.qubit_spec import QubitSpectroscopy
from qcrew.measure.resonator_characterization.rr_spec import RRSpectroscopy

import numpy as np
import h5py
import time

# -------------------------------- Execution -----------------------------------

if __name__ == "__main__":

    current_start = -10.5e-3
    current_stop = -13e-3
    current_step = -0.1e-3
    current_sweep = np.arange(current_start, current_stop, current_step)

    qubit_lo_start = 5.8e9 #6.57e9
    qubit_lo_stop = 5.1e9
    qubit_lo_step = -400e6
    qubit_lo_sweep = np.arange(qubit_lo_start, qubit_lo_stop, qubit_lo_step)

    # Store information in lists to print later
    filename_list = []
    current_list = []
    lo_list = []
    rr_if_list = []

    # Initialize database for compiling whole experimental data
    with Stagehand() as stage:

        db = initialise_database(
            exp_name="qubit_spec_current_sweep",
            sample_name=stage.sample_name,
            project_name=stage.project_name,
            path=stage.datapath,
        )

        with DataSaver(db) as datasaver:
            experiment_no = 1
            for current in current_sweep:

                # Change value of current source
                yoko = stage.YOKO
                # yoko.source = "current"
                yoko.ramp(current, yoko.level, 0.02e-3)  # set output to nominal value

                # Find resonator resonant frequency
                ## Do RR spectroscopy
                x_start = -53e6
                x_stop = -48.5e6
                x_step = 0.1e6

                rr_spec_parameters = {
                    "modes": [stage.RR],
                    "reps": 3000,
                    "wait_time": 10000,
                    "x_sweep": (int(x_start), int(x_stop + x_step / 2), int(x_step)),
                    "fit_fn": None,
                    "fetch_period": 2,
                }

                rr_spec_plot_parameters = {
                    "xlabel": "Resonator pulse frequency (Hz)",
                }

                rr_spec = RRSpectroscopy(**rr_spec_parameters)
                rr_spec.setup_plot(**rr_spec_plot_parameters)
                plotter = Plotter(rr_spec.plot_setup)

                # prof.run_with_stage(rr_spec, stage)
                stderr = (None, None, None)
                qua_program = rr_spec.QUA_sequence()
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
                    stderr = rr_spec.estimate_sd(
                        stats, partial_results, num_results, stderr
                    )

                    # post-process and live plot available results
                    rr_spec_data = rr_spec.plot_results(
                        plotter, partial_results, num_results, stderr
                    )
                    # prevent over-fetching, over-saving, ultra-fast plotting
                    time.sleep(rr_spec.fetch_period)

                z_avg = np.array(rr_spec_data["Z_AVG"])
                frequencies = np.array(rr_spec_data["x"])
                ## Get frequency of MAXIMUM transmission (transmission measurement)
                # rr_if = frequencies[np.argmax(z_avg)]
                ## Get frequency of MINIMUM transmission (reflection measurement)
                rr_if = frequencies[np.argmin(z_avg)]

                stage.RR.int_freq = float(rr_if)  # update RR IF

                # proceed with qubit spectroscopy
                for qubit_lo in qubit_lo_sweep:

                    ## Change qubit LO
                    stage.QUBIT.lo_freq = qubit_lo

                    x_start = -200e6
                    x_stop = 200e6
                    x_step = 0.6e6

                    qubit_spec_parameters = {
                        "modes": [stage.QUBIT, stage.RR],
                        "reps": 4000,
                        "wait_time": 10000,
                        "x_sweep": (
                            int(x_start),
                            int(x_stop + x_step / 2),
                            int(x_step),
                        ),
                        "qubit_op": "constant_pi_pulse",
                        "fit_fn": None,
                        "fetch_period": 6,
                    }

                    qubit_spec_plot_parameters = {
                        "xlabel": "Qubit pulse frequency (Hz) (LO = %.3f GHz)"
                        % (qubit_lo / 1e9),
                    }

                    qubit_spec = QubitSpectroscopy(**qubit_spec_parameters)
                    qubit_spec.setup_plot(**qubit_spec_plot_parameters)
                    plotter = Plotter(qubit_spec.plot_setup)

                    ##### run qubit spectroscopy #####
                    # prof.run_with_stage(qubit_spec, stage)
                    stderr = (None, None, None)
                    qua_program = qubit_spec.QUA_sequence()
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
                        stderr = qubit_spec.estimate_sd(
                            stats, partial_results, num_results, stderr
                        )

                        # post-process and live plot available results
                        qubit_spec_data = qubit_spec.plot_results(
                            plotter, partial_results, num_results, stderr
                        )
                        # prevent over-fetching, over-saving, ultra-fast plotting
                        time.sleep(qubit_spec.fetch_period)

                    ## Correct floor of z_avg
                    z_avg = np.array(qubit_spec_data["Z_AVG"])
                    z_avg -= np.average(z_avg)
                    z_avg = list(z_avg)
                    if current_step < 0:
                        z_avg.reverse()

                    ## Get frequencies
                    freqs = np.array(qubit_spec_data["x"]) + qubit_lo
                    freqs = list(freqs)
                    if current_step < 0:
                        freqs.reverse()

                    # save data
                    exp_tag = "exp_%d" % experiment_no
                    current_sweep_data = {
                        "current": float(current),
                        "qubit_LO": float(qubit_lo),
                        "Z_AVG": np.array(z_avg),
                        "freqs": np.array(freqs),
                    }

                    datasaver.add_multiple_results(
                        current_sweep_data,
                        save=current_sweep_data.keys(),
                        group="data/" + exp_tag,
                    )

                    experiment_no += 1

            yoko = stage.YOKO
            # yoko.ramp(0e-3, yoko.level, 0.02e-3)
            # yoko.state = False
