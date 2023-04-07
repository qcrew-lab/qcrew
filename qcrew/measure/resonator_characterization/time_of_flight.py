""" Time of flight experiment """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np

reps = 20000


def get_qua_program(rr):
    with qua.program() as raw_adc_avg:
        adc_stream = qua.declare_stream(adc_trace=True)
        n = qua.declare(int)

        with qua.for_(n, 0, n < reps, n + 1):
            qua.reset_phase(rr.name)
            qua.measure("readout_pulse" * qua.amp(1), rr.name, adc_stream)
            qua.wait(10000, rr.name)

        with qua.stream_processing():
            adc_stream.input1().average().save("adc_results")
            adc_stream.input1().average().fft().save("adc_fft")

    return raw_adc_avg


if __name__ == "__main__":

    with Stagehand() as stage:

        rr = stage.RR

        # Execute script
        qm = stage.QM
        job = stage.QM.execute(get_qua_program(rr))  # play IF to mode

        handle = job.result_handles
        handle.wait_for_all_values()
        results = handle.get("adc_results").fetch_all()
        results_fft = handle.get("adc_fft").fetch_all()
        pulse_len = rr.readout_pulse.length
        results_fft = np.sqrt(np.sum(np.squeeze(results_fft) ** 2, axis=1)) / pulse_len
        freqs = np.arange(0, 0.5, 1 / pulse_len)[:] * 1e9
        amps = results_fft[: int(np.ceil(pulse_len / 2))]

        fig, axes = plt.subplots(2, 1)

        axes[0].plot(results / 2 ** 12)
        axes[1].plot(freqs[5:] / 1e6, amps[5:])
        np.savez("y2", results)
        print(results[996:1008] / 2 ** 12)
        # Retrieving and plotting FFT data.
        plt.show()
