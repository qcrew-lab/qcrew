""" """

import numpy as np
from scipy import signal

import qcrew.control.modes as qcm
import qcrew.control.pulses as qcp

# from qcrew.control.pulses import integration_weights
from qcrew.helpers import logger

from qm import _Program
from qm import qua
from qm.QuantumMachine import QuantumMachine

ADC_TO_VOLTS = 2 ** -12


class ReadoutTrainer:
    """ """

    def __init__(self, rr: qcm.Mode, qubit: qcm.Mode, qm: QuantumMachine, params: dict):
        """ """
        self._rr: qcm.Mode = rr
        self._qubit: qcm.Mode = qubit
        self._qm: QuantumMachine = qm
        self.params = params

        logger.info(f"Initialized ReadoutTrainer with {self._rr} and {self._qubit}")

    def train(self) -> None:
        """
        Obtain integration weights of rr given the excited and ground states of qubit and update rr mode.
        """

        # Start with constant integration weights. Not necessary, really
        self._reset_weights()

        trace_g_list, timestamps_g = self._acquire_traces(excite_qubit=False)
        env_g = self._calc_average_envelope(ADC_TO_VOLTS * trace_g_list, timestamps_g)

        trace_e_list, timestamps_e = self._acquire_traces(excite_qubit=True)
        env_e = self._calc_average_envelope(ADC_TO_VOLTS * trace_e_list, timestamps_e)

        # Get discrimination threshold
        threshold = self._get_threshold(env_g, env_e)

        # Get difference between envelopes and normalize
        envelope_diff = env_g - env_e

        # Normalize and squeeze envelope_diff by 1/4th
        norm = np.max(np.abs(envelope_diff))
        norm_envelope_diff = envelope_diff / norm
        squeezed_diff = self._squeeze_array(norm_envelope_diff)  # convert shape

        self._update_weights(squeezed_diff, threshold)

        return env_g, env_e

    def _reset_weights(self):
        """
        Start the pulse with constant integration weights
        """
        integration_weights = qcp.OptimizedIntegrationWeights(
            length=int(self._rr.readout_pulse.length / 4)
        )
        self._rr.readout_pulse.integration_weights = integration_weights

    def _acquire_traces(self, excite_qubit: bool = False) -> tuple[list]:
        """
        Run QUA program to obtain traces of the readout pulse.
        """

        job = self._qm.execute(self._get_qua_program(excite_qubit))

        handle = job.result_handles
        handle.wait_for_all_values()
        timestamps = handle.get("timestamps").fetch_all()["value"]
        adc = handle.get("adc").fetch_all()["value"]

        return adc, timestamps

    def _get_qua_program(self, excite_qubit: bool = False) -> _Program:
        """ """
        reps = self.params["reps"]
        wait_time = self.params["wait_time"]
        readout_pulse = self.params["readout_pulse"]
        qubit_pi_pulse = self.params["qubit_pi_pulse"]

        with qua.program() as acquire_traces:
            adc = qua.declare_stream(adc_trace=True)
            n = qua.declare(int)

            with qua.for_(n, 0, n < reps, n + 1):

                qua.measure(readout_pulse, self._rr.name, adc)
                qua.wait(wait_time, self._rr.name)
                # qua.reset_phase(self._rr.name)

                if excite_qubit:
                    qua.align(self._rr.name, self._qubit.name)
                    self._qubit.play(qubit_pi_pulse)
                    qua.align(self._rr.name, self._qubit.name)

                qua.measure(readout_pulse, self._rr.name, adc)
                qua.wait(wait_time, self._rr.name)

            with qua.stream_processing():
                # streams for envelope calculation
                adc.input1().timestamps().save_all("timestamps")
                adc.input1().save_all("adc")

                # streams for plotting/bug fixing
                adc.input1().average().save("adc_avg")
                adc.input1().average().fft().save("adc_fft")

        return acquire_traces

    def _calc_average_envelope(self, trace_list, timestamps):
        int_freq = np.abs(self._rr.int_freq)

        # demodulate
        s = trace_list * np.exp(1j * 2 * np.pi * int_freq * 1e-9 * (timestamps - 36))

        # filter 2*omega_IF using hann filter
        hann = signal.hann(int(2 * 1e9 / int_freq), sym=True)
        hann = hann / np.sum(hann)
        s_filtered = np.array([np.convolve(s_single, hann, "same") for s_single in s])

        # adjust envelope
        env = 2 * s_filtered.conj()

        # get average envelope
        avg_env = np.average(env, axis=0)

        return avg_env

    def _squeeze_array(self, s):
        """
        Split the array in bins of 4 values and average them. QM requires the weights to have 1/4th of the length of the readout pulse.
        """
        return np.average(np.reshape(s, (-1, 4)), axis=1)

    def _update_weights(self, squeezed_diff, threshold):

        # Update the threshold
        self._rr.readout_pulse(threshold=threshold)

        weights = {}
        weights["I"] = np.array(
            [np.real(squeezed_diff).tolist(), (np.imag(squeezed_diff)).tolist()]
        )
        weights["Q"] = np.array(
            [np.imag(-squeezed_diff).tolist(), np.real(squeezed_diff).tolist()]
        )

        path = self.params["weights_file_path"]

        # Save weights to npz file
        np.savez(path, **weights)

        # Update the readout pulse with the npz file path
        self._rr.readout_pulse.integration_weights(path=path)

    def _get_threshold(self, env_g, env_e):

        norm = np.max(np.abs(np.concatenate((env_g, env_e))))

        # The square of Frobenius norm of the raw weights
        bias_g = (np.linalg.norm(env_g) ** 2) / 2 * 4
        bias_e = (np.linalg.norm(env_e) ** 2) / 2 * 4

        threshold = bias_e - bias_g
        print(threshold)

        return threshold
