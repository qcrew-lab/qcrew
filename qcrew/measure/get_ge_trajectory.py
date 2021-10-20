""" get ge state trajectory v5 """

import matplotlib.pyplot as plt
from qm.QuantumMachinesManager import QuantumMachinesManager
from qcrew.control import Stagehand
from qm import qua
import numpy as np
from qcrew.helpers import time_difference
from qcrew.helpers.discriminator import StateDiscriminator
from qcrew.helpers.dc_offset import DCoffsetCalibrator
from qcrew.helpers.time_difference import TimeDiffCalibrator
from pathlib import Path

reps = 1000
wait_time = 400000
readout_length = 500
pad = 3000
readout_pulse = "readout_pulse"
# NOTE: if the envelope has wired startind and ending, dc_offset need to be updated
# Refer to dc_offset.py
dc_offset = 0.020341857986814565
analog_input = 1
path = Path("C:/Users/qcrew/qcrew/qcrew/config") / "opt_readout_weights.npz"


def get_qua_program(rr, qubit):
    with qua.program() as ge_trajectory:
        adcg = qua.declare_stream(adc_trace=True)
        adce = qua.declare_stream(adc_trace=True)
        n = qua.declare(int)

        with qua.for_(n, 0, n < reps, n + 1):

            qua.update_frequency(rr.name, int(-50e6))

            qua.align(rr.name, qubit.name)
            qua.reset_phase(rr.name)
            qua.measure(readout_pulse * qua.amp(1), rr.name, adcg)
            qua.wait(wait_time, rr.name)

            qua.update_frequency(rr.name, int(-49e6))

            qua.align(rr.name, qubit.name)
            qua.play("pi" * qua.amp(1), qubit.name)
            qua.align(rr.name, qubit.name)
            qua.measure(readout_pulse * qua.amp(1), rr.name, adce)
            qua.wait(wait_time, rr.name)

        with qua.stream_processing():
            adcg.input1().timestamps().save_all("timestamps_g")
            adce.input1().timestamps().save_all("timestamps_e")
            adcg.input1().save_all("adc_g")
            adce.input1().save_all("adc_e")

            adcg.input1().average().save("adc_g_avg")
            adcg.input1().average().fft().save("adc_g_fft")
            adce.input1().average().save("adc_e_avg")
            adce.input1().average().fft().save("adc_e_fft")

    return ge_trajectory


if __name__ == "__main__":

    with Stagehand() as stage:

        rr = stage.RR
        qubit = stage.QUBIT
        rr.readout_pulse(const_length=readout_length, ampx=1.0, pad=pad)

        config = stage.QM.get_config()
        config = DCoffsetCalibrator.update_dc_offset(
            offset=dc_offset, config=config, qe=rr.name, analog_input=analog_input
        )

        qmm = QuantumMachinesManager()
        qm = qmm.open_qm(config)
        job = qm.execute(get_qua_program(rr, qubit))

        handle = job.result_handles
        handle.wait_for_all_values()

        timestamps_g = handle.get("timestamps_g").fetch_all()["value"]
        timestamps_e = handle.get("timestamps_e").fetch_all()["value"]
        adc_g = handle.get("adc_g").fetch_all()["value"]
        adc_e = handle.get("adc_e").fetch_all()["value"]
        timestamps = np.concatenate((timestamps_g, timestamps_e), axis=0)
        adc = np.concatenate((adc_g, adc_e), axis=0)

        # td = TimeDiffCalibrator(qmm, config, rr.name)
        # time_diff = td.calibrate()
        # print("Time difference: ", time_diff)

        sd = StateDiscriminator(resonator=rr.name, config=config, time_diff=None)
        env = sd.get_envelopes(adc=adc, ts=timestamps)
        sd.plot(env[0], title="The envelope for g state")
        sd.plot(env[1], title="The envelope for e state")

        weights, threshold = sd.get_weights_threshold(env)
        rr.opt_readout_pulse(threshold=threshold)

        np.savez(path, **weights)
        rr.opt_readout_pulse.integration_weights(path=path)
