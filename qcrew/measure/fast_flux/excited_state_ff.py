""" Time of flight experiment """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np
from scipy.optimize import curve_fit

from qcrew.control.instruments.meta.readout_trainer import ReadoutTrainer
from qcrew.analyze import fit


def calculate_confusion_matrix(Ig_list, Ie_list, threshold):
    pgg = 100 * round((np.sum(Ig_list > threshold) / len(Ig_list)), 3)
    pge = 100 * round((np.sum(Ig_list < threshold) / len(Ig_list)), 3)
    pee = 100 * round((np.sum(Ie_list < threshold) / len(Ie_list)), 3)
    peg = 100 * round((np.sum(Ie_list > threshold) / len(Ie_list)), 3)
    return {"pgg": pgg, "pge": pge, "pee": pee, "peg": peg}


def fit_hist_double_gaussian(guess, data_g):
    """
    The E population is estimated from the amplitudes of the two gaussians
    fitted from the G state blob.
    """
    p0 = [
        guess["x0"].value,
        guess["x1"].value,
        guess["a0"],
        guess["a1"],
        # guess["ofs"],
        guess["sigma"].value,
    ]
    print(p0)

    lower_bound = [
        min(data_g["xs"]),
        min(data_g["xs"]),
        0.0,
        0.0,
        min(data_g["xs"]) - max(data_g["xs"]),
    ]
    upper_bound = [
        max(data_g["xs"]),
        max(data_g["xs"]),
        1.5 * max(data_g["ys"]),
        1.5 * max(data_g["ys"]),
        max(data_g["xs"]) - min(data_g["xs"]),
    ]

    popt, _ = curve_fit(
        double_gaussian,
        data_g["xs"],
        data_g["ys"],
        bounds=(lower_bound, upper_bound),
        p0=p0,
    )
    return popt


def double_gaussian(xs, x0, x1, a0, a1, sigma):
    """
    Gaussian defined by it's area <area>, sigma <s>, position <x0> and
    y-offset <ofs>.
    """
    r0 = (xs - x0) ** 2
    r1 = (xs - x1) ** 2
    ys = a0 * np.exp(-0.5 * r0 / sigma ** 2) + a1 * np.exp(-0.5 * r1 / sigma ** 2)
    return ys


def fit_IQ_blob(I_list, Q_list):

    fit_fn = "gaussian2d_symmetric"

    # Make ground IQ blob in a 2D histogram
    zs, xs, ys = np.histogram2d(I_list, Q_list, bins=50)

    # Replace "bin edge" by "bin center"
    dx = xs[1] - xs[0]
    xs = (xs - dx / 2)[1:]
    dy = ys[1] - ys[0]
    ys = (ys - dy / 2)[1:]

    # Get fit to 2D gaussian
    xs_grid, ys_grid = np.meshgrid(xs, ys)
    params = fit.do_fit(fit_fn, xs_grid.T, ys_grid.T, zs=zs)
    fit_zs = fit.eval_fit(fit_fn, params, xs_grid.T, ys_grid.T).T

    data = {
        "I_grid": xs_grid,
        "Q_grid": ys_grid,
        "counts": zs,
        "counts_fit": fit_zs,
    }

    return params, data


reps = 20000
wait_time = int(60e3)


def get_qua_program(
    rr,
    qubit,
    flux,
    qubit_pulse,
    flux_pulse,
    flux_amp,
    readout_delay,
    excite_qubit=False,
):
    with qua.program() as acquire_IQ:
        I = qua.declare(qua.fixed)
        Q = qua.declare(qua.fixed)
        n = qua.declare(int)

        with qua.for_(n, 0, n < reps, n + 1):

            flux.play(flux_pulse, ampx=flux_amp)
            qua.wait(int(readout_delay // 4), qubit.name, rr.name)

            if excite_qubit:
                # qua.align(self._rr.name, self._qubit.name)
                qubit.play(qubit_pulse)
                qua.align(rr.name, qubit.name)

            rr.measure((I, Q))
            qua.save(I, "I")
            qua.save(Q, "Q")
            qua.wait(wait_time, rr.name)

    return acquire_IQ


if __name__ == "__main__":

    with Stagehand() as stage:

        rr, qubit, flux = stage.RR, stage.QUBIT, stage.FLUX
        qm = stage.QM

        flux_pulse_list = [
            "predist_pulse_50",
            "predist_pulse_298",
        ]
        flux_amp_list = np.arange(-0.35, 0.36, 0.01)
        e_population_list = []

        for flux_pulse in flux_pulse_list:
            for flux_amp in flux_amp_list:
                print(flux_amp, flux_pulse)
                # Get IQ for qubit in ground state
                IQ_acquisition_program = get_qua_program(
                    rr,
                    qubit,
                    flux,
                    "gaussian_pi",
                    flux_pulse,
                    flux_amp,
                    1100,
                    excite_qubit=False,
                )
                job = qm.execute(IQ_acquisition_program)
                handle = job.result_handles
                handle.wait_for_all_values()
                Ig_list = handle.get("I").fetch_all()["value"]
                Qg_list = handle.get("Q").fetch_all()["value"]

                # Get IQ for qubit in excited state
                IQ_acquisition_program = get_qua_program(
                    rr,
                    qubit,
                    flux,
                    "gaussian_pi",
                    flux_pulse,
                    flux_amp,
                    1100,
                    excite_qubit=True,
                )
                job = qm.execute(IQ_acquisition_program)
                handle = job.result_handles
                handle.wait_for_all_values()
                Ie_list = handle.get("I").fetch_all()["value"]
                Qe_list = handle.get("Q").fetch_all()["value"]

                # Fit each blob to a 2D gaussian and retrieve the center
                params_g, data_g = fit_IQ_blob(Ig_list, Qg_list)
                params_e, data_e = fit_IQ_blob(Ie_list, Qe_list)

                IQ_center_g = (params_g["x0"], params_g["y0"])  # G blob center
                IQ_center_e = (params_e["x0"], params_e["y0"])  # E blob center

                # Calculate threshold (does not update readout threshold value)
                threshold = (IQ_center_g[0] + IQ_center_e[0]) / 2
                # Calculates the confusion matrix of the readout
                conf_matrix = calculate_confusion_matrix(Ig_list, Ie_list, threshold)

                # # Plot scatter and contour of each blob
                # fig, ax = plt.subplots(figsize=(7, 7))
                # ax.set_aspect("equal")
                # ax.scatter(Ig_list, Qg_list, label="|g>", s=5)
                # ax.scatter(Ie_list, Qe_list, label="|e>", s=5)
                # ax.contour(
                #     data_g["I_grid"],
                #     data_g["Q_grid"],
                #     data_g["counts_fit"],
                #     levels=5,
                #     cmap="winter",
                # )
                # ax.contour(
                #     data_e["I_grid"],
                #     data_e["Q_grid"],
                #     data_e["counts_fit"],
                #     levels=5,
                #     cmap="autumn",
                # )
                # ax.plot(
                #     [threshold, threshold],
                #     [np.min(data_g["Q_grid"]), np.max(data_g["Q_grid"])],
                #     label="threshold",
                #     c="k",
                #     linestyle="--",
                # )

                # ax.set_title("IQ blobs for each qubit state")
                # ax.set_ylabel("Q")
                # ax.set_xlabel("I")
                # ax.legend()
                # plt.show()

                # Plot I histogram
                fig, ax = plt.subplots(figsize=(7, 4))
                n_g, bins_g, _ = ax.hist(Ig_list, bins=50, alpha=1)
                n_e, bins_e, _ = ax.hist(Ie_list, bins=50, alpha=0.8)

                # Estimate excited state population from G blob double gaussian fit

                pge = (
                    conf_matrix["pge"] / 100
                )  # first estimate of excited state population
                guess = {
                    "x0": params_g["x0"],
                    "x1": params_e["x0"],
                    "a0": max(n_g),
                    "a1": max(n_g) * pge / (1 - pge),
                    "ofs": 0.0,
                    "sigma": params_g["sigma"],
                }
                data_hist_g = {"xs": (bins_g[1:] + bins_g[:-1]) / 2, "ys": n_g}

                popt = fit_hist_double_gaussian(guess, data_hist_g)
                a0 = popt[2]
                a1 = popt[3]
                e_population = a1 / (a1 + a0)
                e_population_list.append(e_population)
                print("Excited state population: ", e_population)

                ax.plot(bins_g, [double_gaussian(x, *popt) for x in bins_g])

                ax.set_title("Projection of the IQ blobs onto the I axis")
                ax.set_ylabel("counts")
                ax.set_xlabel("I")
                ax.legend()
                plt.show()

                # Organize the raw I and Q data for each G and E measurement
                data = {
                    "Ig": Ig_list,
                    "Qg": Qg_list,
                    "Ie": Ie_list,
                    "Qe": Qe_list,
                }
        e_population = np.array(e_population_list).reshape(
            len(flux_pulse_list), len(flux_amp_list)
        )
        plt.ylabel("Excited state population")
        plt.xlabel("Flux pulse amplitude")
        for line in range(e_population.shape[0]):
            plt.plot(flux_amp_list, e_population[line], label=flux_pulse_list[line])
        plt.legend()
        plt.show()
