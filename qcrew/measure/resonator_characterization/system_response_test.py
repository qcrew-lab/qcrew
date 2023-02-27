""" Time of flight experiment """

from black import re
import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np

reps = 10000


def get_qua_program(rr):
    with qua.program() as raw_adc_avg:
        adc_stream = qua.declare_stream(adc_trace=True)
        n = qua.declare(int)

        with qua.for_(n, 0, n < reps, n + 1):
            qua.reset_phase(rr.name)
            qua.measure("readout_pulse" * qua.amp(1), rr.name, adc_stream)
            qua.wait(20000, rr.name)

        with qua.stream_processing():
            adc_stream.input1().average().save("adc_results")

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
        inverted_results = -1 * results
        plt.plot(inverted_results)

        np.savez(
            "C:\\Users\\qcrew\\Documents\\line_impulse_response\\10k_avg_long_tail_inverted.npz",
            results,
        )
        # Retrieving and plotting FFT data.
        plt.show()
