import time

from qcrew.control import professor as prof
import qcrew.measure.qua_macros as macros
from qm import qua

from qcrew.measure.weak_dispersive.char_func_1D_preselection_hk_vac import (
    char_func_1D_preselection_hk_vac,
)

from qcrew.measure.weak_dispersive.char_func_1D_preselect_hk_coh import (
    char_func_1D_preselect_hk_coh,
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
        # vac
        char_1D_parameter_vac = {
            "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
            "reps": 5000,  # 25000
            "wait_time": 1e6,
            "fetch_period": 60,  # time between data fetching rounds in sec
            "delay": 120,  # 188,  # wait time between opposite sign displacements
            "corrected_phase": 0.335006,
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
        # without pi2 pulse
        char_1D_parameter_coh = {
            "modes": ["QUBIT", "CAVITY", "RR", "FLUX"],
            "reps": 5000,
            "wait_time": 1e6,
            "fetch_period": 60,  # time between data fetching rounds in sec
            "delay": 120,  # wait time between opposite sign displacements
            "corrected_phase": 0.335006,
            "x_sweep": (
                x_start,
                x_stop + x_step / 2,
                x_step,
            ),
            # "y_sweep": (y_start, y_stop + y_step / 2, y_step),
            "qubit_pi": "gaussian_pi_short_ecd",
            "qubit_pi2": "gaussian_pi2_short_ecd",
            "qubit_evolution": "gaussian_pi2_hk",
            "char_func_displacement": "ecd2_displacement",
            "cav_state_op": "_",
            "measure_real": True,
            "single_shot": True,
            # "plot_quad": "I_AVG",  # measure real part of char function if True, imag Part if false
        }

        plot_parameters = {
            "xlabel": "X",  # beta of (ECD(beta))
            "ylabel": "Y",
            "plot_type": "2D",
            "cmap": "bwr",
            "plot_err": False,
            "skip_plot": True,
        }

        char_1D_experiment_vac = char_func_1D_preselection_hk_vac(**char_1D_parameter_vac)
        char_1D_experiment_vac.setup_plot(skip_plot=True)

        prof.run(char_1D_experiment_vac)

        time.sleep(20)

        char_1D_experiment_1 = char_func_1D_preselect_hk_coh(
            **char_1D_parameter_coh
        )
        char_1D_experiment_1.setup_plot(skip_plot=True)

        prof.run(char_1D_experiment_1)

        time.sleep(20)
