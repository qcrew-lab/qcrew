""" get ge state trajectory v5 """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np
from qcrew.helpers.state_discriminator.TwoStateDiscriminator import (
    TwoStateDiscriminator,
)

reps = 200000
wait_time = 200000
readout_length = 600


def get_qua_program(rr, qubit):
    with qua.program() as ge_trajectory:
        adcg = qua.declare_stream(adc_trace=True)
        adce = qua.declare_stream(adc_trace=True)
        n = qua.declare(int)

        with qua.for_(n, 0, n < reps, n + 1):
            qua.align(rr.name, qubit.name)
            # qua.reset_phase(rr.name)
            qua.measure("readout_pulse" * qua.amp(1), rr.name, adcg)
            qua.wait(wait_time, rr.name)

            qua.align(rr.name, qubit.name)
            qua.play("pi" * qua.amp(1), qubit.name)
            qua.align(rr.name, qubit.name)
            qua.measure("readout_pulse" * qua.amp(1), rr.name, adce)
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
        rr.readout_pulse(length=readout_length, ampx=1.0)
        rr.time_of_flight = 500  # 248

        qmm = stage._qmm
        config = stage.QM.get_config()

        con_name = config["elements"][rr.name]["outputs"]["out1"][0]
        config["controllers"][con_name]["analog_inputs"][1] = {
            "offset": 0.021990265869140626
        }

        qm = qmm.open_qm(config)
        # Execute script
        job = qm.execute(get_qua_program(rr, qubit))

        handle = job.result_handles
        handle.wait_for_all_values()

        timestamps_g = handle.get("timestamps_g").fetch_all()["value"]
        timestamps_e = handle.get("timestamps_e").fetch_all()["value"]
        adc_g = handle.get("adc_g").fetch_all()["value"]
        adc_e = handle.get("adc_e").fetch_all()["value"]

        adc_g_avg = handle.get("adc_g_avg").fetch_all()
        adc_g_fft = handle.get("adc_g_fft").fetch_all()

        adc_e_avg = handle.get("adc_e_avg").fetch_all()
        adc_e_fft = handle.get("adc_e_fft").fetch_all()

        timestamps = np.concatenate((timestamps_g, timestamps_e), axis=0)
        adc = np.concatenate((adc_g, adc_e), axis=0)

        #####################################################################
        g_pulse_len = len(adc_g_avg)
        g_results_fft = (
            np.sqrt(np.sum(np.squeeze(adc_g_fft) ** 2, axis=1)) / g_pulse_len
        )
        g_amps = g_results_fft[: int(np.ceil(g_pulse_len / 2))]
        g_freqs = (
            np.arange(0, (1 / g_pulse_len) * len(g_amps), 1 / g_pulse_len)[:] * 1e9
        )

        fig, axes = plt.subplots(2, 1)
        print("adc length:", len(adc_g_avg))
        axes[0].set_title("g state adc trace")
        axes[0].plot(adc_g_avg)
        axes[1].set_title("g state fft")
        axes[1].plot(g_freqs[5:] / 1e6, g_amps[5:])
        fig.tight_layout()
        plt.show()

        e_pulse_len = len(adc_e_avg)
        e_results_fft = (
            np.sqrt(np.sum(np.squeeze(adc_e_fft) ** 2, axis=1)) / e_pulse_len
        )
        e_amps = e_results_fft[: int(np.ceil(e_pulse_len / 2))]
        e_freqs = (
            np.arange(0, (1 / e_pulse_len) * len(e_amps), 1 / e_pulse_len)[:] * 1e9
        )

        fig, axes = plt.subplots(2, 1)
        print("adc length:", len(adc_e_avg))
        axes[0].set_title("e state adc trace")
        axes[0].plot(adc_e_avg)
        axes[1].set_title("e state fft")
        axes[1].plot(e_freqs[5:] / 1e6, e_amps[5:])
        fig.tight_layout()
        plt.show()
        #######################################################################

        rr_freq = rr.int_freq
        time_diff = 36
        smearing = 0

        x_demod = adc
        ts_demod = timestamps

        train = TwoStateDiscriminator(
            qmm,
            config,
            resonator="RR",
            resonator_pulse="readout_pulse",
            qubit="QUBIT",
            qubit_pulse="pi",
        )
        sig = train._downconvert(x_demod, ts_demod)

        fig, axes = plt.subplots(3, 1)
        print("sig shape:", len(sig))
        axes[0].set_title("sig abs")
        axes[0].plot(np.abs(sig[0]))
        axes[1].set_title("sig real")
        axes[1].plot(np.real(sig[0]))
        axes[2].set_title("sig imag")
        axes[2].plot(np.imag(sig[0]))
        fig.tight_layout()
        plt.show()

        sig_avg = np.mean(sig)
        fig, axes = plt.subplots(3, 1)
        print("sig shape:", len(sig))
        axes[0].set_title("sig abs")
        axes[0].plot(np.abs(sig[0]))
        axes[1].set_title("sig real")
        axes[1].plot(np.real(sig[0]))
        axes[2].set_title("sig imag")
        axes[2].plot(np.imag(sig[0]))
        fig.tight_layout()
        plt.show()

        seq0 = np.array([[i] * reps for i in range(2)]).flatten()

        traces = train._get_traces(
            qe="RR",
            correction_method="none",
            seq0=seq0,
            I_res=[],
            Q_res=[],
            sig=sig,
            use_hann_filter=True,
        )
        plt.figure()
        plt.plot(np.real(traces[0]), label="real trace for g")
        plt.plot(np.imag(traces[0]), label="imag trace for g")
        plt.legend()
        plt.show()

        plt.figure()
        plt.plot(np.real(traces[1]), label="real trace for e")
        plt.plot(np.imag(traces[1]), label="imag trace for e")
        plt.legend()
        plt.show()

        weights = train._quantize_traces(traces)

        # normalization
        # ``norm`` is the maximal absolute value of the weights
        norm = np.max(np.abs(weights))
        weights = weights / norm

        plt.figure()
        plt.plot(np.real(weights[0]), label="real trace for g")
        plt.plot(np.imag(weights[0]), label="imag trace for g")
        plt.legend()
        plt.show()

        plt.figure()
        plt.plot(np.real(weights[1]), label="real trace for e")
        plt.plot(np.imag(weights[1]), label="imag trace for e")
        plt.legend()
        plt.show()

        # The square of Frobenius norm of the raw weights

        bias = (np.linalg.norm(weights * norm, axis=1) ** 2) / norm / 2 * (2 ** -24) * 4
        saved_data = {"weights": weights, "bias": bias}
