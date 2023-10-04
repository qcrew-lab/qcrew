""" Time of flight experiment with envelope calculation """

import matplotlib.pyplot as plt
from qcrew.control import Stagehand
from qm import qua
import numpy as np
from scipy import signal

reps = 100000  # 50000


def get_qua_program(rr, qubit):
    with qua.program() as raw_adc_avg:
        adc_stream = qua.declare_stream(adc_trace=True)
        n = qua.declare(int)

        with qua.for_(n, 0, n < reps, n + 1):
            # qua.reset_phase(rr.name)
            qubit.play("qubit_gaussian_120ns_pi_pulse")
            qua.align(qubit.name, rr.name)
            qua.measure("readout_pulse", rr.name, adc_stream)
            qua.wait(125000, rr.name)

        with qua.stream_processing():
            adc_stream.input1().timestamps().save_all("timestamps")
            adc_stream.input1().save_all("adc")  # raw_adc
            # adc_stream.input1().average().save("adc_avg") # adc_avg
            # adc_stream.input1().average().fft().save("adc_fft")

    return raw_adc_avg


if __name__ == "__main__":

    with Stagehand() as stage:

        rr, qubit = stage.RR, stage.QUBIT

        # Execute script
        job = stage.QM.execute(get_qua_program(rr, qubit))  # play IF to mode

        # get all the trace info from experiment
        # trace_g_list, timestamps_g = self._acquire_traces(self._qm, excite_qubit=False)
        ADC_TO_VOLTS = 2 ** -12  # convert to voltage
        TS = 1e-9  # Sampling time of the OPX in seconds
        T_OFS = 35.96
        handle = job.result_handles
        
        # Fetching data, converting the 12 bit ADC value to voltage and removing extra dimensions.
        raw_adc = np.squeeze(handle.adc.fetch_all()["value"] / 2**12)
        
        handle.wait_for_all_values()
        timestamps = handle.get("timestamps").fetch_all()["value"]
        trace_list = ADC_TO_VOLTS * handle.get("adc").fetch_all()["value"] # Converting the 12 bit ADC value to voltage
        # results = handle.get("adc_avg").fetch_all()
        # results_fft = handle.get("adc_fft").fetch_all()

        int_freq = np.abs(rr.int_freq)
        # demodulate
        s = trace_list * np.exp(1j * 2 * np.pi * int_freq * TS * (timestamps - T_OFS))

        # filter 2*omega_IF using hann filter
        hann = signal.hann(int(2 / TS / int_freq), sym=True)
        hann = hann / np.sum(hann)
        s_filtered = np.array([np.convolve(s_single, hann, "same") for s_single in s])

        # adjust envelope
        env = 2 * s_filtered.conj()

        # get average envelope
        avg_env = np.average(env, axis=0)
 
        # Plot envelopes
        fig, axes = plt.subplots(2, 1, figsize=(7, 10))  # , sharex=True
        axes[0].plot(1000 * np.real(avg_env), label="Re")
        axes[0].plot(1000 * np.imag(avg_env), label="Imag")
        axes[0].set_title("|e> envelope")
        axes[0].set_ylabel("Amplitude (mV)")
        axes[0].legend()
        axes[1].plot(1000 * np.real(avg_env), 1000 * np.imag(avg_env))
        axes[1].set_title("I+jQ")
        # axes[1].set_ylabel("Amplitude (mV)")
        axes[1].legend()
        plt.show()
        np.savez(
            "D:/data/YABBAv4/20230916/tof_e_square_2400_pad900_p0.3_int50.9.npz",
            raw_adc = raw_adc,
            real=1000 * np.real(avg_env),
            imag=1000 * np.imag(avg_env),
            avg_env=avg_env,
            timestamps=timestamps,
            T_OFS=T_OFS,
            int_freq = int_freq,
            trace_list = trace_list,
        )