import time

from qcrew.control import professor as prof
import qcrew.measure.qua_macros as macros
from qm import qua

from qcrew.measure.cavity_experiments.sq_cat_decay_6db import sq_cat_decay_6db
from qcrew.measure.cavity_experiments.sq_cat_decay_3db import sq_cat_decay_3db

if __name__ == "__main__":

    ntimes = 10

    x_start = -1.7  # -1.4
    x_stop = 1.7
    x_step = 0.1

    y_start = -1.7
    y_stop = 1.7
    y_step = 0.1

    ## 3db_ [ 1.38744578  0.51199234 -0.19874056 -0.46461027 -0.3244084  -0.65943663]
    # V_cat amp = 1.274302411891448

    decay_sweep = [1000, 50000, 100000, 150000, 200000]
    for k in range(ntimes):
        for n in range(len(decay_sweep)):
            # for n in range(24):
            sq_3db_parameter = {
                "modes": [
                    "QUBIT",
                    "CAV",
                    "RR",
                ],
                "reps": 100,
                "wait_time": 2e6,  # 50e3,
                "fetch_period": 4,  # time between data fetching rounds in sec
                "delay": 80,  # 160,  # 100# wait time between opposite sign displacements
                "u1_amp_scale": 1.38744578,
                "v1_amp_scale": 0.51199234,
                "u2_amp_scale": -0.19874056,
                "v2_amp_scale": -0.46461027,
                "u3_amp_scale": -0.3244084,
                "v3_amp_scale": -0.65943663,
                "ecd_amp_scale": 1,
                "u_cat_amp_scale": 0.8495,  # # 1.2743*2/3
                "decay_time": decay_sweep[n],
                "x_sweep": (
                    x_start,
                    x_stop + x_step / 2,
                    x_step,
                ),  # ampitude sweep of the displacement pulses in the ECD
                "y_sweep": (y_start, y_stop + y_step / 2, y_step),
                "qubit_pi2": "pi2",
                "qubit_pi": "pi",
                "char_func_displacement": "constant_cos_ECD_3",
                "cav_ecd_displace": "constant_cos_ECD_1",
                "cav_ecd_displace_special": "constant_cos_ECD_2",
                "cat_cav_ecd_displace": "constant_cos_ECD_3",
                "cav_displace_1": "constant_cos_cohstate_1",
                "measure_real": True,
                "plot_quad": "I_AVG",
                "single_shot": False,
            }

            ## 6db_[-0.57844852 0.60452584 -2.15238317 -0.30349575 0.67163186 0.88878487]

            sq_6db_parameter = {
                "modes": [
                    "QUBIT",
                    "CAV",
                    "RR",
                ],
                "reps": 100,
                "wait_time": 2e6,  # 50e3,
                "fetch_period": 4,  # time between data fetching rounds in sec
                "delay": 80,  # 160,  # 100# wait time between opposite sign displacements
                "u1_amp_scale": -0.5784,
                "v1_amp_scale": 0.6045,
                "u2_amp_scale": -1.0762,  # -2.15238/2
                "v2_amp_scale": -0.30349,
                "u3_amp_scale": 0.67163,
                "v3_amp_scale": 0.88878,
                "ecd_amp_scale": 1,
                "u_cat_amp_scale": 0.6014,  # # 0.90213*2/3
                "decay_time": decay_sweep[n],
                "x_sweep": (
                    x_start,
                    x_stop + x_step / 2,
                    x_step,
                ),  # ampitude sweep of the displacement pulses in the ECD
                "y_sweep": (y_start, y_stop + y_step / 2, y_step),
                "qubit_pi2": "pi2",
                "qubit_pi": "pi",
                "char_func_displacement": "constant_cos_ECD_3",
                "cav_ecd_displace": "constant_cos_ECD_1",
                "cav_ecd_displace_special": "constant_cos_ECD_2",
                "cat_cav_ecd_displace": "constant_cos_ECD_3",
                "cav_displace_1": "constant_cos_cohstate_1",
                "measure_real": True,
                "plot_quad": "I_AVG",
                "single_shot": False,
            }

            plot_parameters = {
                "xlabel": "X",  # beta of (ECD(beta))
                "ylabel": "Y",
                "plot_type": "2D",
                "cmap": "bwr",
                "plot_err": False,
                "skip_plot": True,
            }

            sq_3db_experiment = sq_cat_decay_3db(**sq_3db_parameter)
            sq_3db_experiment.setup_plot(**plot_parameters)

            prof.run(sq_3db_experiment)

            time.sleep(20)

            sq_6db_experiment = sq_cat_decay_6db(**sq_6db_parameter)
            sq_6db_experiment.setup_plot(**plot_parameters)

            prof.run(sq_6db_experiment)

            time.sleep(20)
