import time

from qcrew.control import professor as prof
import qcrew.measure.qua_macros as macros
from qm import qua


from qcrew.analyze import stats
from qcrew.analyze.plotter import Plotter
from qcrew.control import Stagehand
from qcrew.control.instruments.qm import QMResultFetcher
from qcrew.helpers import logger
from qcrew.helpers.datasaver import DataSaver, initialise_database
from qcrew.measure.experiment import Experiment
import matplotlib.pyplot as plt
import numpy as np
from qcrew.analyze import fit


from qcrew.measure.automatic_calibration.auto_tune_qubit_ff import (
    QubitSpectroscopy,
)

from qcrew.measure.weak_dispersive.char_func_1D_qua_macro_ff import (
    char_func_1D_qua_macro_ff,
)
from qcrew.measure.weak_dispersive.char_func_2D_qua_macro_ff import (
    char_func_2D_qua_macro_ff,
)

if __name__ == "__main__":

    ntimes = 200

    x_start = -1.90
    x_stop = 1.91
    x_step = 0.1

    y_start = -1.9
    y_stop = 1.91
    y_step = 0.1
    
    spec_min = -60e6
    spec_max = -40e6
    spec_step = 0.2e6

    for k in range(ntimes):
        
        freq_target = -50.0e6

        slope = 378.4e9
        current_max = -2.275e-3
        current_min = -2.3e-3
        current_step = 0.0001e-3

        spec_min = -60e6
        spec_max = -40e6
        spec_step = 0.2e6

        parameters_qubit_spec = {
            "modes": ["QUBIT", "RR", "CAVITY", "FLUX"],
            "reps": 5000,
            "wait_time": 60e3,
            "x_sweep": (int(spec_min), int(spec_max + spec_step / 2), int(spec_step)),
            "qubit_op": "gaussian_pi_400_lk",
            # "single_shot": True,
            "plot_quad": "I_AVG",
            "fit_fn": "gaussian",
        }

        plot_parameters = {"skip_plot": False, "plot_err": False}

        with Stagehand() as stage:
            qm = stage.QM
            yoko = stage.YOKO

            # Check qubit frequency
            parameters_qubit_spec["modes"] = [stage.QUBIT, stage.RR, stage.CAVITY, stage.FLUX]
            experiment_check_qubit_freq = QubitSpectroscopy(**parameters_qubit_spec)
            experiment_check_qubit_freq.setup_plot(**plot_parameters)
            qua_program = experiment_check_qubit_freq.QUA_sequence()
            qm_job = qm.execute(qua_program)

            fetcher = QMResultFetcher(handle=qm_job.result_handles)
            stderr = (
                None,
                None,
                None,
            )  # to hold running (stderr, mean, variance * (n-1))

            db = initialise_database(
                exp_name=experiment_check_qubit_freq.name,
                sample_name=stage.sample_name,
                project_name=stage.project_name,
                path=stage.datapath,
            )

            experiment_check_qubit_freq.filename = db.filename
            plotter = Plotter(experiment_check_qubit_freq.plot_setup)
            with DataSaver(db) as datasaver:
                datasaver.add_metadata(experiment_check_qubit_freq.parameters)
                for mode in stage.modes:
                    datasaver.add_metadata(mode.parameters)
                while fetcher.is_fetching:
                    partial_results = fetcher.fetch()
                    num_results = fetcher.count
                    if not partial_results:  # empty dict means no new results available
                        continue
                    datasaver.update_multiple_results(
                        partial_results,
                        save=experiment_check_qubit_freq.live_saving_tags,
                        group="data",
                    )
                    stderr = ([],)
                    qubit_spec_data = experiment_check_qubit_freq.plot_results(
                        plotter, partial_results, num_results, stderr
                    )
                    time.sleep(experiment_check_qubit_freq.fetch_period)

                ##################         SAVE REMAINING DATA         #####################

                datasaver.add_multiple_results(
                    qubit_spec_data, save=qubit_spec_data.keys(), group="data"
                )
                state = np.array(qubit_spec_data["I_AVG"])
                freqs = np.array(qubit_spec_data["x"])
                params = fit.do_fit("gaussian", freqs, state)
                qubit_freq = float(params["x0"].value)

                ### Calculate current to get target qubit frequency
                current_initial = yoko.level
                current_target = current_initial + (freq_target - qubit_freq) / slope
                if current_max > current_target > current_min:
                    yoko.ramp(current_target, yoko.level, np.abs(current_step))

                print("Changed YOKO bias to ", current_target)

    
        char_1D_parameter = {
            "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
            "reps": 100,
            "wait_time": 1e6,
            "fetch_period": 5,  # time between data fetching rounds in sec
            "delay": 120,  # 188,  # wait time between opposite sign displacements
            "x_sweep": (x_start, x_stop + x_step / 2, x_step),
            "y_sweep": (0, 1),
            "qubit_pi": "gaussian_pi_short_ecd",
            "qubit_pi2": "gaussian_pi2_short_ecd",
            "char_func_displacement": "ecd2_displacement",
            "cav_state_op": "_",
            "fit_fn": "gaussian",
            "measure_real": True,
            "single_shot": True,
            # "plot_quad": "I_AVG",  # measure real part of char function if True, imag Part if false
        }
        
        char_2D_parameter = {
            "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
            "reps": 100,
            "wait_time": 1e6,
            "fetch_period": 120,  # time between data fetching rounds in sec
            "delay": 120,  # wait time between opposite sign displacements
            "x_sweep": (
                x_start,
                x_stop + x_step / 2,
                x_step,
            ),
            "y_sweep": (y_start, y_stop + y_step / 2, y_step),
            "qubit_pi": "gaussian_pi_short_ecd",
            "qubit_pi2": "gaussian_pi2_short_ecd",
            "char_func_displacement": "ecd2_displacement",
            "cav_state_op": "_",
            "measure_real": False,
            "single_shot": True,
            # "plot_quad": "I_AVG",  # measure real part of char function if True, imag Part if false
        }

        # plot_parameters = {
        #     "xlabel": "X",  # beta of (ECD(beta))
        #     "ylabel": "Y",
        #     "plot_type": "2D",
        #     "cmap": "bwr",
        #     "plot_err": False,
        #     "skip_plot": False,
        # }
        
        plot_2d_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        "ylabel": "Y",
        "plot_type": "2D",
        "cmap": "bwr",
        # "skip_plot": True,
        }
        
        plot_1d_parameters = {
        "xlabel": "X",  # beta of (ECD(beta))
        # "ylabel": "Y",
        # "plot_type": "2D",
        "cmap": "bwr",
        }

        time.sleep(20)
        

        char_1D_experiment = char_func_1D_qua_macro_ff(**char_1D_parameter)
        char_1D_experiment.setup_plot(**plot_1d_parameters)

        prof.run(char_1D_experiment)

        time.sleep(20)
        
        
        # check qubit freq before 2d
        with Stagehand() as stage:
            qm = stage.QM
            yoko = stage.YOKO

            # Check qubit frequency
            parameters_qubit_spec["modes"] = [stage.QUBIT, stage.RR, stage.CAVITY, stage.FLUX]
            experiment_check_qubit_freq = QubitSpectroscopy(**parameters_qubit_spec)
            experiment_check_qubit_freq.setup_plot(**plot_parameters)
            qua_program = experiment_check_qubit_freq.QUA_sequence()
            qm_job = qm.execute(qua_program)

            fetcher = QMResultFetcher(handle=qm_job.result_handles)
            stderr = (
                None,
                None,
                None,
            )  # to hold running (stderr, mean, variance * (n-1))

            db = initialise_database(
                exp_name=experiment_check_qubit_freq.name,
                sample_name=stage.sample_name,
                project_name=stage.project_name,
                path=stage.datapath,
            )

            experiment_check_qubit_freq.filename = db.filename
            plotter = Plotter(experiment_check_qubit_freq.plot_setup)
            with DataSaver(db) as datasaver:
                datasaver.add_metadata(experiment_check_qubit_freq.parameters)
                for mode in stage.modes:
                    datasaver.add_metadata(mode.parameters)
                while fetcher.is_fetching:
                    partial_results = fetcher.fetch()
                    num_results = fetcher.count
                    if not partial_results:  # empty dict means no new results available
                        continue
                    datasaver.update_multiple_results(
                        partial_results,
                        save=experiment_check_qubit_freq.live_saving_tags,
                        group="data",
                    )
                    stderr = ([],)
                    qubit_spec_data = experiment_check_qubit_freq.plot_results(
                        plotter, partial_results, num_results, stderr
                    )
                    time.sleep(experiment_check_qubit_freq.fetch_period)

                ##################         SAVE REMAINING DATA         #####################

                datasaver.add_multiple_results(
                    qubit_spec_data, save=qubit_spec_data.keys(), group="data"
                )
                state = np.array(qubit_spec_data["I_AVG"])
                freqs = np.array(qubit_spec_data["x"])
                params = fit.do_fit("gaussian", freqs, state)
                qubit_freq = float(params["x0"].value)

                ### Calculate current to get target qubit frequency
                current_initial = yoko.level
                current_target = current_initial + (freq_target - qubit_freq) / slope
                if current_max > current_target > current_min:
                    yoko.ramp(current_target, yoko.level, np.abs(current_step))

                print("Changed YOKO bias to ", current_target)
        
        time.sleep(20)
       
        #2D

        char_2D_experiment = char_func_2D_qua_macro_ff(**char_2D_parameter)
        char_2D_experiment.setup_plot(**plot_2d_parameters)

        prof.run(char_2D_experiment)

        time.sleep(20)
