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

    simplex: np.ndarray = np.array([[0.0, 0.0], [0.0, 0.1], [0.1, 0.0]])
    threshold: float = 2.0  # in dBm
    maxiter: int = 100
    span: float = 2e6
    rbw: float = 50e3
    ref_power: float = 0.0

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

        trace_g_list, timestamps_g = self._acquire_traces(excite_qubit=False)
        env_g = self._calc_average_envelope(ADC_TO_VOLTS * trace_g_list, timestamps_g)

        trace_e_list, timestamps_e = self._acquire_traces(excite_qubit=True)
        env_e = self._calc_average_envelope(ADC_TO_VOLTS * trace_e_list, timestamps_e)

        weights = env_g - env_e
        squeezed_weights = self._squeeze_weights(weights)  # convert to useful shape

        self._update_weights(squeezed_weights)

        return env_g, env_e, weights, squeezed_weights

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
        s = trace_list * np.exp(1j * 2 * np.pi * int_freq * 1e-9 * timestamps)

        # filter 2*omega_IF using hann filter
        hann = signal.hann(int(2 * 1e9 / int_freq), sym=True)
        hann = hann / np.sum(hann)
        s_filtered = np.array([np.convolve(s_single, hann, "same") for s_single in s])

        # adjust envelope
        env = 2 * s_filtered.conj()

        # get average envelope
        avg_env = np.average(env, axis=0)

        return avg_env

    def _squeeze_weights(self, weights):
        """
        Split the weights in bins of 4 values and average them. QM requires the weights to have 1/4th of the length of the readout pulse.
        """
        return np.average(np.reshape(weights, (-1, 4)), axis=1)

    def _update_weights(self, weights):

        path = self.params["weights_file_path"]
        # Save weights to npz file
        np.savez(path, weights)
        # self._rr.opt_readout_pulse(threshold=threshold)
        # self._rr.readout_pulse.integration_weights(path=path)
        # integration_weights = qcp.OptimizedIntegrationWeights(len(weights), path)

        # integration_weights = qcp.ConstantIntegrationWeights()
        # readout_pulse = qcp.ReadoutPulse(
        #    length=int(10000),
        #    const_length=int(10000),
        #    ampx=0,
        #    integration_weights=integration_weights,
        # )
