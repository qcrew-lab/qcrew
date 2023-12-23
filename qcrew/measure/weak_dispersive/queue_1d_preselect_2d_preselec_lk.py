import time

from qcrew.control import professor as prof
import qcrew.measure.qua_macros as macros
from qm import qua

from qcrew.measure.weak_dispersive.char_func_1D_preselection_lk_vac import (
    char_func_1D_preselection_lk_vac,
)
from qcrew.measure.weak_dispersive.char_func_2D_chi_preselect_lk_coh import (
    char_func_2D_chi_preselect_lk_coh,
)

if __name__ == "__main__":

    ntimes = 20

    x_start = -1.90
    x_stop = 1.91
    x_step = 0.1

    y_start = -1.9
    y_stop = 1.91
    y_step = 0.1

    for k in range(ntimes):

        char_1D_parameter = {
            "modes": ["QUBIT", "CAVITY", "RR", "FLUX", "QUBIT_LK"],
            "reps": 5000,  # 25000
            "wait_time": 1e6,
            "fetch_period": 20,  # time between data fetching rounds in sec
            "delay": 120,  # 188,  # wait time between opposite sign displacements
            "corrected_phase": 0.526591,
            "x_sweep": (x_start, x_stop + x_step / 2, x_step),
            "y_sweep": (0, 1),
            "qubit_pi": "gaussian_pi_short_ecd",
            "qubit_pi2": "gaussian_pi2_short_ecd",
            "char_func_displacement": "ecd2_displacement",
            "cav_state_op": "_",
            "fit_fn": "gaussian",
            "measure_real": True,
            "single_shot": True,
        }

        char_2D_parameter = {
            "modes": ["QUBIT", "CAVITY", "RR", "FLUX", "QUBIT_LK"],
            "reps": 5000,
            "wait_time": 1e6,
            "fetch_period": 60,  # time between data fetching rounds in sec
            "delay": 120,  # wait time between opposite sign displacements
            "corrected_phase": 0.526591,
            "x_sweep": (
                x_start,
                x_stop + x_step / 2,
                x_step,
            ),
            "y_sweep": (y_start, y_stop + y_step / 2, y_step),
            "qubit_pi": "gaussian_pi_short_ecd",
            "qubit_pi2": "gaussian_pi2_short_ecd",
            "qubit_evolution": "gaussian_pi2_lk",
            "char_func_displacement": "ecd2_displacement",
            "cav_state_op": "_",
            "measure_real": True,
            "single_shot": True,
        }

        plot_parameters = {
            "xlabel": "X",  # beta of (ECD(beta))
            "ylabel": "Y",
            "plot_type": "2D",
            "cmap": "bwr",
            "plot_err": False,
            "skip_plot": True,
        }

        char_1D_experiment = char_func_1D_preselection_lk_vac(**char_1D_parameter)
        char_1D_experiment.setup_plot(skip_plot=True)

        prof.run(char_1D_experiment)

        time.sleep(20)

        char_2D_experiment = char_func_2D_chi_preselect_lk_coh(**char_2D_parameter)
        char_2D_experiment.setup_plot(skip_plot=True)

        prof.run(char_2D_experiment)

        time.sleep(20)
