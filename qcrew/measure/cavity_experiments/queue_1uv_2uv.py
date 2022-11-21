import time

from qcrew.control import professor as prof
import qcrew.measure.qua_macros as macros
from qm import qua

from qcrew.measure.cavity_experiments.ECD_char_postselect import ECDcharpostselect
from qcrew.measure.qubit_experiments_GE.T2_virtual_detuning import T2

if __name__ == "__main__":

    ntimes = 400

    x_start = -1.2
    x_stop = 1.2
    x_step = 0.03

    y_start = -1.2
    y_stop = 1.2
    y_step = 0.03


    u_cat_amp_scale = 1
    ecd_amp_scale = 1

    for k in range(ntimes):
        
        u1_amp_scale = 1
        v1_amp_scale = -0.6
        u2_amp_scale = 1.319
        v2_amp_scale = 0.30
        u3_amp_scale = -0.91
        v3_amp_scale = -0.80
        
        post_select_parameter_1uv = {
            "modes": ["QUBIT", "CAV", "RR"],
            "reps": 200,
            "wait_time": 4e6,  # 50e3,
            "fetch_period": 4,  # time between data fetching rounds in sec
            "delay": 80,  # 160,  # 100# wait time between opposite sign displacements
            "u1_amp_scale": u1_amp_scale,
            "v1_amp_scale": v1_amp_scale,
            "u2_amp_scale": u2_amp_scale,
            "v2_amp_scale": v2_amp_scale,
            "u3_amp_scale": u3_amp_scale,
            "v3_amp_scale": v3_amp_scale,
            "ecd_amp_scale": ecd_amp_scale,
            "u_cat_amp_scale": u_cat_amp_scale,
            "x_sweep": (
                x_start,
                x_stop + x_step / 2,
                x_step,
            ),  # ampitude sweep of the displacement pulses in the ECD
            "y_sweep": (y_start, y_stop + y_step / 2, y_step),
            "qubit_pi2": "pi2",
            "qubit_pi": "pi",
            "char_func_displacement": "constant_cos_ECD_2",
            "cav_ecd_displace": "constant_cos_ECD_2_alpha0.5",
            "cav_ecd_displace_special": "constant_cos_ECD_2_alpha1",
            "cat_cav_ecd_displace": "constant_cos_ECD_2_alpha1",
            "cav_displace_1": "constant_cos_cohstate_1",
            "measure_real": True,
            "plot_quad": "I_AVG",
            "single_shot": False,
        }
        
        
        
        
        
        

        post_select_parameter_2uv = {
            "modes": ["QUBIT", "RR", "QUBIT_EF"],
            "reps": 4000,
            "wait_time": 80000,
            "x_sweep": (int(4), int(3000 + 40 / 2), int(40)),
            "qubit_op": "pi2",
            "detuning": int(0.5e6),
            "extra_vars": {
                "phase": macros.ExpVariable(
                    var_type=qua.fixed,
                    tag="phase",
                    average=True,
                    buffer=True,
                    save_all=True,
                )
            },
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

        t2_experiment = T2(**t2_parameters)
        t2_experiment.setup_plot(skip_plot=True)

        prof.run(t2_experiment)

        time.sleep(20)

        ecd_experiment = ECDcharpostselect(**post_select_parameter)
        ecd_experiment.setup_plot(**plot_parameters)

        prof.run(ecd_experiment)

        time.sleep(20)
