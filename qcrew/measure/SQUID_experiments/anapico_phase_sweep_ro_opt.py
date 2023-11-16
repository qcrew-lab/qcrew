""" Readout integration weights training for single-shot readout """

from cmath import phase
from qcrew.control.instruments.meta.readout_trainer import ReadoutTrainer, T_OFS
from qcrew.control import Stagehand
from qcrew.helpers.datasaver import DataSaver, initialise_database

from pathlib import Path
import numpy as np
import time
import matplotlib.pyplot as plt
import qcrew.control.pulses as qcp

phase_sweep = np.arange(70, 75, 0.1)

IQ_BLOBS_PATH = "C:\\Users\\qcrew\\Desktop\\anapico_phase_sweep_fine_70_75_0.1\\iq_plots"
HISTORGRAM_PATH = "C:\\Users\\qcrew\\Desktop\\anapico_phase_sweep_fine_70_75_0.1\\histogram"
THRESHOLDS_PATH = "C:\\Users\\qcrew\\Desktop\\anapico_phase_sweep_fine_70_75_0.1\\thresholds"
CONF_MAT_PATH = "C:\\Users\\qcrew\\Desktop\\anapico_phase_sweep_fine_70_75_0.1\\conf_matrix.npz"
CONF_PLOT_PATH = "C:\\Users\\qcrew\\Desktop\\anapico_phase_sweep_fine_70_75_0.1\\conf_plot.png"


def calculate_threshold(trainer, exp_name):

    # Get IQ for qubit in ground state
    IQ_acquisition_program = trainer._get_QUA_IQ_acquisition()
    job = trainer._qm.execute(IQ_acquisition_program)
    handle = job.result_handles
    handle.wait_for_all_values()
    Ig_list = handle.get("I").fetch_all()["value"]
    Qg_list = handle.get("Q").fetch_all()["value"]

    # Get IQ for qubit in excited state
    IQ_acquisition_program = trainer._get_QUA_IQ_acquisition(excite_qubit=True)
    job = trainer._qm.execute(IQ_acquisition_program)
    handle = job.result_handles
    handle.wait_for_all_values()
    Ie_list = handle.get("I").fetch_all()["value"]
    Qe_list = handle.get("Q").fetch_all()["value"]

    # Fit each blob to a 2D gaussian and retrieve the center
    params_g, data_g = trainer._fit_IQ_blob(Ig_list, Qg_list)
    params_e, data_e = trainer._fit_IQ_blob(Ie_list, Qe_list)

    IQ_center_g = (params_g["x0"], params_g["y0"])  # G blob center
    IQ_center_e = (params_e["x0"], params_e["y0"])  # E blob center

    # Calculate threshold
    threshold = (IQ_center_g[0] + IQ_center_e[0]) / 2

    # Update readout with optimal threshold
    trainer._update_threshold(threshold)

    # Calculates the confusion matrix of the readout
    conf_matrix = trainer._calculate_confusion_matrix(Ig_list, Ie_list, threshold)

    # Plot scatter and contour of each blob
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_aspect("equal")
    ax.scatter(Ig_list, Qg_list, label="|g>", s=5)
    ax.scatter(Ie_list, Qe_list, label="|e>", s=5)
    ax.contour(
        data_g["I_grid"],
        data_g["Q_grid"],
        data_g["counts_fit"],
        levels=5,
        cmap="winter",
    )
    ax.contour(
        data_e["I_grid"],
        data_e["Q_grid"],
        data_e["counts_fit"],
        levels=5,
        cmap="autumn",
    )
    ax.plot(
        [threshold, threshold],
        [np.min(data_g["Q_grid"]), np.max(data_g["Q_grid"])],
        label="threshold",
        c="k",
        linestyle="--",
    )

    ax.set_title(f"IQ blobs for {exp_name}")
    ax.set_ylabel("Q")
    ax.set_xlabel("I")
    ax.legend()
    plt.savefig(f"{IQ_BLOBS_PATH}/{exp_name}.png")
    # plt.show()

    # Plot I histogram
    fig, ax = plt.subplots(figsize=(7, 4))
    n_g, bins_g, _ = ax.hist(Ig_list, bins=50, alpha=1)
    n_e, bins_e, _ = ax.hist(Ie_list, bins=50, alpha=0.8)

    # Estimate excited state population from G blob double gaussian fit

    pge = conf_matrix["pge"]  # first estimate of excited state population
    guess = {
        "x0": params_g["x0"],
        "x1": params_e["x0"],
        "a0": max(n_g),
        "a1": max(n_g) * pge / (1 - pge),
        "ofs": 0.0,
        "sigma": params_g["sigma"],
    }
    data_hist_g = {"xs": (bins_g[1:] + bins_g[:-1]) / 2, "ys": n_g}
    ax.set_title(f"Histogram for {exp_name}")
    ax.legend()
    plt.savefig(f"{HISTORGRAM_PATH}/{exp_name}.png")
    # plt.show()

    # Organize the raw I and Q data for each G and E measurement
    data = {
        "Ig": Ig_list,
        "Qg": Qg_list,
        "Ie": Ie_list,
        "Qe": Qe_list,
    }

    return threshold, conf_matrix, data


if __name__ == "__main__":
    start = time.time()
    pgg_list = []
    pge_list = []
    peg_list = []
    pee_list = []
    for phase_val in phase_sweep:
        with Stagehand() as stage:
            rr, qubit = stage.RR, stage.QUBIT
            qm = stage.QM
            anapico = stage.APUASYN
            # anapico.channel = 1

            anapico.phase = f"{phase_val} deg"
            # ensure that modulation for channels 1 & 3 are off
            anapico.off_all_modulation(1)
            anapico.off_all_modulation(3)
            # Integration weights training
            weight_file_path = f"{phase_val}_phase_opt_weights.npz"
            file_path = Path(
                f"C:\\Users\\qcrew\\Desktop\\qcrew\\qcrew\\config\\weights\\{weight_file_path}"
            )

            params = {
                "reps": 10000,
                "wait_time": 80000,  # cc 5e3 cc= 20000ns qubit t1:
                "qubit_pi_pulse": "gaussian_pi",  # pulse to excite qubit
                "weights_file_path": file_path,
            }

            integration_weights = qcp.OptimizedIntegrationWeights(
                length=int(rr.readout_pulse.length / 4)
            )
            rr.readout_pulse.integration_weights = integration_weights

            ro_trainer = ReadoutTrainer(rr, qubit, qm, **params)
            ro_trainer.train_weights()
        with Stagehand() as stage:
            rr, qubit = stage.RR, stage.QUBIT
            qm = stage.QM
            weight_file_path = f"{phase_val}_phase_opt_weights.npz"
            file_path = Path(
                f"C:\\Users\\qcrew\\Desktop\\qcrew\\qcrew\\config\\weights\\{weight_file_path}"
            )

            params = {
                "reps": 10000,
                "wait_time": 80000,  # cc 5e3 cc= 20000ns qubit t1:
                "qubit_pi_pulse": "gaussian_pi",  # pulse to excite qubit
                "weights_file_path": file_path,
            }
            ro_trainer = ReadoutTrainer(rr, qubit, qm, **params)
            threshold, conf_matrix, data = calculate_threshold(ro_trainer, phase_val)

            pgg = conf_matrix["pgg"]
            pge = conf_matrix["pge"]
            peg = conf_matrix["peg"]
            pee = conf_matrix["pee"]

            pgg_list.append(pgg)
            pge_list.append(pge)
            peg_list.append(peg)
            pee_list.append(pee)

            with open(f"{THRESHOLDS_PATH}\\{phase_val}.txt", "w") as f:
                f.write(f"threshold={threshold},")
                f.write(f"pgg = {pgg},")
                f.write(f"pge = {pge},")
                f.write(f"peg = {peg},")
                f.write(f"pee = {pee},")

            ## Save data
            db = initialise_database(
                exp_name=f"threshold_calculation_{phase_val}",
                sample_name=stage.sample_name,
                project_name=stage.project_name,
                path=stage.datapath,
            )
            with DataSaver(db) as datasaver:

                # add metadata dictionary
                datasaver.add_metadata(ro_trainer.parameters)

                datasaver.add_multiple_results(data, save=data.keys(), group="data")
    with open(CONF_MAT_PATH, "wb") as f:
        np.savez(f, pgg=pgg_list, pge=pge_list, peg=peg_list, pee=pee_list)

    fig, axs = plt.subplots(2, 2)
    axs[0, 0].plot(phase_sweep, pgg_list)
    axs[0, 0].set_title("pgg")
    axs[0, 1].plot(phase_sweep, pge_list, "tab:orange")
    axs[0, 1].set_title("pge")
    axs[1, 0].plot(phase_sweep, peg_list, "tab:green")
    axs[1, 0].set_title("peg")
    axs[1, 1].plot(phase_sweep, pee_list, "tab:red")
    axs[1, 1].set_title("pee")
    plt.savefig(CONF_PLOT_PATH)

    end = time.time()
    print(end - start)
