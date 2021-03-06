""" Time of flight experiment with envelope calculation """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np
from scipy import signal

reps = 5000


def get_qua_program(rr, qubit):
    with qua.program() as raw_adc_avg:
        adc_stream = qua.declare_stream(adc_trace=True)
        n = qua.declare(int)

        with qua.for_(n, 0, n < reps, n + 1):
            qubit.play("constant_pulse")
            qua.align(qubit.name, rr.name)
            qua.measure("readout_pulse" * qua.amp(1.0), rr.name, adc_stream)
            qua.wait(400000, rr.name)

        with qua.stream_processing():
            adc_stream.input1().average().save("adc_results")
            adc_stream.input1().average().fft().save("adc_fft")

    return raw_adc_avg


if __name__ == "__main__":

    with Stagehand() as stage:

        rr, qubit = stage.RR, stage.QUBIT

        # Execute script
        job = stage.QM.execute(get_qua_program(rr, qubit))  # play IF to mode

        handle = job.result_handles
        handle.wait_for_all_values()
        results = handle.get("adc_results").fetch_all()
        results_fft = handle.get("adc_fft").fetch_all()
        pulse_len = rr.readout_pulse.length
        results_fft = np.sqrt(np.sum(np.squeeze(results_fft) ** 2, axis=1)) / pulse_len
        freqs = np.arange(0, 0.5, 1 / pulse_len)[:] * 1e9
        amps = results_fft[: int(np.ceil(pulse_len / 2))]

        fig, axes = plt.subplots(3, 1)

        t_rel = np.linspace(0, pulse_len - 1, pulse_len)
        sig = (results) * np.exp(1j * (2 * np.pi * rr.int_freq * 1e-9 * t_rel + 0.0))
        period_ns = int(1 / np.abs(rr.int_freq) * 1e9)
        hann = signal.hann(period_ns * 2, sym=True)

        hann = hann / np.sum(hann)
        demod_sig = np.convolve(sig, hann, "same")

        sig_fft = np.fft.fft(np.real(sig))
        amps_sig = sig_fft[: int(np.ceil(pulse_len / 2))]
        demod_fft = np.fft.fft(np.real(demod_sig))
        amps_demod = demod_fft[: int(np.ceil(pulse_len / 2))]

        axes[0].plot(results / 2 ** 12)
        axes[1].plot(freqs[0:] / 1e6, amps_sig[0:])

        # This is the envelope of the average trace. In ge-discriminator
        # we take the average of the envelopes of each single trace
        axes[2].plot(np.real(demod_sig))
        axes[2].plot(np.imag(demod_sig))

        # Retrieving and plotting FFT data.
        plt.show()
