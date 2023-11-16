""" get iq blob of g and e """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np
from scipy import signal

reps = 5000 # 50000


def get_qua_program(rr, qubit):
    with qua.program() as acquire_IQ:
        # adc_stream = qua.declare_stream(adc_trace=True)
        n = qua.declare(int)
        I = qua.declare(qua.fixed)
        Q = qua.declare(qua.fixed)


        with qua.for_(n, 0, n < reps, n + 1):
            # qua.reset_phase(rr.name)
            qubit.play("gaussian_pi")
            qua.align(qubit.name, rr.name)
            # qua.measure("readout_pulse", rr.name, adc_stream)
            rr.measure((I, Q))  # measure transmitted signal
            qua.save(I, "I")
            qua.save(Q, "Q")
            qua.wait(20000, rr.name)

        # with qua.stream_processing():
        #     adc_stream.input1().timestamps().save_all("timestamps")
        #     adc_stream.input1().save_all("adc") #raw_adc
        #     # adc_stream.input1().average().save("adc_avg") # adc_avg
        #     # adc_stream.input1().average().fft().save("adc_fft")

    return acquire_IQ


if __name__ == "__main__":

    with Stagehand() as stage:

        rr, qubit = stage.RR, stage.QUBIT

        # Execute script
        job = stage.QM.execute(get_qua_program(rr, qubit))  # play IF to mode
        
        # Get IQ for qubit in ground state
        handle = job.result_handles
        handle.wait_for_all_values()
        I_list = handle.get("I").fetch_all()["value"]
        Q_list = handle.get("Q").fetch_all()["value"]

    # Plot scatter and contour of each blob
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.set_aspect("equal")
        ax.scatter(I_list, Q_list, label="|e>", s=5)
        
        ax.set_title("IQ blobs for each qubit state")
        ax.set_ylabel("Q")
        ax.set_xlabel("I")
        ax.legend()
        plt.show()
        np.savez('C:/Users/qcrew/Documents/Candace/somerset_tof/optimize/IQ_e_square_900.npz',
            real= I_list, imag = Q_list)
