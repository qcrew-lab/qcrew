""" get ge state trajectory v5 """

from qcrew.control import Stagehand
from qm import qua
import numpy as np
from qcrew.measure.state_discriminator.helpers.discriminator import (
    histogram_plot,
    fidelity_plot,
)

num_of_states = 2
reps = 5000

wait_time = 300000
readout_pulse = "readout_pulse"
analog_input = 1
out = "out1"


def get_qua_program(rr, qubit, threshold):
    with qua.program() as ge_discrimination:
        Ig = qua.declare(qua.fixed)
        Qg = qua.declare(qua.fixed)
        Ie = qua.declare(qua.fixed)
        Qe = qua.declare(qua.fixed)
        resg = qua.declare(bool)
        rese = qua.declare(bool)
        n = qua.declare(int)

        with qua.for_(n, 0, n < reps, n + 1):
            qua.align(rr.name, qubit.name)

            rr.measure((Ig, Qg))

            qua.assign(resg, Ig > threshold)
            qua.save(resg, "resg")
            qua.save(Ig, "Ig")
            qua.save(Qg, "Qg")
            qua.wait(wait_time, rr.name)

            qua.align(rr.name, qubit.name)
            qua.play("pi", qubit.name)
            qua.align(rr.name, qubit.name)

            rr.measure((Ie, Qe))

            qua.assign(rese, Ie > threshold)
            qua.save(rese, "rese")
            qua.save(Ie, "Ie")
            qua.save(Qe, "Qe")

            qua.wait(wait_time, rr.name)
    return ge_discrimination


if __name__ == "__main__":

    with Stagehand() as stage:

        rr = stage.RR
        qubit = stage.QUBIT

        state_seq = np.array([[i] * reps for i in range(num_of_states)]).flatten()

        job = stage.QM.execute(get_qua_program(rr, qubit, 0))

        handle = job.result_handles
        handle.wait_for_all_values()

        Ig_res = handle.get("Ig").fetch_all()["value"]
        Ie_res = handle.get("Ie").fetch_all()["value"]
        I_res = np.concatenate((Ig_res, Ie_res), axis=0)

        Qg_res = handle.get("Qg").fetch_all()["value"]
        Qe_res = handle.get("Qe").fetch_all()["value"]
        Q_res = np.concatenate((Qg_res, Qe_res), axis=0)

        stateg_res = handle.get("resg").fetch_all()["value"]
        statee_res = handle.get("rese").fetch_all()["value"]
        state = np.concatenate((stateg_res, statee_res), axis=0)

        from qcrew.analyze import fit
        import matplotlib.pyplot as plt

        fit_fn = "gaussian2d"

        hist_data_g = plt.hist2d(Ig_res, Qg_res, bins=1000)
        plt.show()
        # get fit parameters
        params = fit.do_fit(fit_fn, Ig_res, Qg_res, hist_data_g)
        fit_zs = fit.eval_fit(fit_fn, params, Ig_res, Qg_res)

        # convert param values into formated string
        param_val_list = [
            key + " = {:.3e}".format(val.value) for key, val in params.items()
        ]
        # Join list in a single block of text
        fit_text = "\n".join(param_val_list)

        # return fit_text, fit_ys

        histogram_plot(
            I_res,
            Q_res,
            state_seq=state_seq,
            num_of_states=num_of_states,
            threshold=5e-5,
        )
