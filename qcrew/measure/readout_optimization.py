""" get ge state trajectory v5 """

import matplotlib.pyplot as plt
from qm.QuantumMachinesManager import QuantumMachinesManager
from qcrew.control import Stagehand
from qm import qua
import numpy as np
from qcrew.helpers import time_difference
from qcrew.helpers.discriminator import (
    StateDiscriminator,
    histogram_plot,
    fidelity_plot,
)
from qcrew.helpers.dc_offset import DCoffsetCalibrator
from qcrew.helpers.time_difference import TimeDiffCalibrator

num_of_states = 2
reps = 10000
wait_time = 400000
readout_length = 500
pad = 3000
readout_pulse = "opt_readout_pulse"
# NOTE: if the envelope has wired startind and ending, dc_offset need to be updated
# Refer to dc_offset.py
dc_offset = 0.020341857986814565
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
            qua.update_frequency(rr.name, int(-50e6))
            qua.align(rr.name, qubit.name)
            qua.measure(
                readout_pulse * qua.amp(1),
                rr.name,
                None,
                qua.demod.full("iw_i", Ig, out),
                qua.demod.full("iw_q", Qg, out),
            )
            qua.assign(resg, Ig > threshold)
            qua.save(resg, "resg")
            qua.save(Ig, "Ig")
            qua.save(Qg, "Qg")
            qua.wait(wait_time, rr.name)

            qua.update_frequency(rr.name, int(-49.5e6))
            qua.align(rr.name, qubit.name)
            qua.play("pi" * qua.amp(1), qubit.name)
            qua.align(rr.name, qubit.name)
            qua.measure(
                readout_pulse * qua.amp(1),
                rr.name,
                None,
                qua.demod.full("iw_i", Ie, out),
                qua.demod.full("iw_q", Qe, out),
            )

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
        rr.opt_readout_pulse(length=readout_length, ampx=1.0, pad=pad)

        thres = rr.opt_readout_pulse.threshold
        state_seq = np.array([[i] * reps for i in range(num_of_states)]).flatten()

        config = stage.QM.get_config()
        config = DCoffsetCalibrator.update_dc_offset(
            offset=dc_offset, config=config, qe=rr.name, analog_input=analog_input
        )

        qmm = QuantumMachinesManager()
        qm = qmm.open_qm(config)
        job = qm.execute(get_qua_program(rr, qubit))

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

        histogram_plot(
            I_res,
            Q_res,
            state_seq=state_seq,
            num_of_states=num_of_states,
            threshold=thres,
        )
        fidelity_plot(res=state, state_seq=state_seq)
