import numpy as np
from pandas import DataFrame
from qm.qua import *
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
from sklearn import mixture
from scipy import signal

from .TimeDiffCalibrator import TimeDiffCalibrator
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig, LoopbackInterface
from typing import Optional, List
from scipy.integrate import simps
import itertools


class StateDiscriminator:
    """
    The state discriminator is a class that generates optimized measure procedure for state discrimination
    of a multi-level qubit.
    .. note:
        Currently only 3-states discrimination is supported. We assume that the setup includes a IQ mixer performing up-conversion
        and a double balanced mixer which apply the down-conversion of the readout pulse.
    """

    def __init__(
        self,
        qmm: QuantumMachinesManager,
        config: dict,
        resonator: Optional[str] = None,
        readout_pulse: Optional[str] = None,
        qubit: Optional[str] = None,
        qubit_pulse: Optional[str] = None,
        analog_input: Optional[str] = None,
        path: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """
        Constructor for the state discriminator class.

        Args:
        qmm: A QuantumMachineManager object
        config: A quantum machine configuration dictionary with the readout resonator element (must be mixInputs
        and has 2 outputs).

        resonator: A string with the name of the readout resonator element (as specified in the config)
        path: A path to save optimized parameters, namely, integration weights and bias for each state. This file
        is generated during training, and it is used during the subsequent measure_state procedure.
        """

        self.qmm = qmm
        self.config = config

        # some default parameters
        self.resonator = resonator or "rr"
        if self.resonator in self.config["elements"]:
            self.readout_pulse = readout_pulse or "readout"

            if (
                self.readout_pulse
                not in self.config["elements"][self.resonator]["operations"]
            ):
                raise ValueError(self.readout_pulse, "dpes not exist in the operations")

            self.time_of_flight = self.config["elements"][self.resonator][
                "time_of_flight"
            ]
            self.smearing = self.config["elements"][self.resonator]["smearing"]
        else:
            raise ValueError(self.resonator, " does not exist in the elements")

        self.qubit = qubit or "qubit"
        if self.qubit in self.config["elements"]:
            self.qubit_pulse = qubit_pulse or "pi"

            if (
                self.qubit_pulse
                not in self.config["elements"][self.qubit]["operations"]
            ):
                raise ValueError(self.qubit_pulse, "dpes not exist in the operations")
        else:
            raise ValueError(self.qubit, " does not exist in the elements")

        self.analog_input = analog_input or "out1"
        if metadata:
            try:
                self.wait_time = metadata["wait_time"] or 500
                self.N = metadata["reps"] or 10
            except:
                raise ValueError(
                    'metadata dictionary does not include the keys "wait_time" or "reps".'
                )
        else:
            self.wait_time = 100
            # the simulator has memory limitation so that N should be small
            self.N = 300

        self.num_of_states = 3  # g e f
        self.path = path
        self.saved_data = None
        self.time_diff = None
        self.finish_train = 0
        self._load_file(path)

    def _load_file(self, path):
        if os.path.isfile(path):

            # load existing weight
            self.saved_data = np.load(path)

            # update configuration
            self._update_config()

    def _get_qe_freq(self, qe):
        return self.config["elements"][qe]["intermediate_frequency"]

    def _add_iw_to_all_pulses(self, iw):
        # iw: integration weight name
        for pulse in self.config["pulses"].values():

            # TODO: need to check, in the example, they used " if 'integration_weights' not in pulse: ""
            # judge whether the pulse is a readout pulse by verifying if the name "integration_weights"
            # is in the pulse keys
            if "integration_weights" in pulse:
                pulse["integration_weights"][iw] = iw

    def _update_config(self):
        weights = self.saved_data["weights"]
        for i in range(self.num_of_states):
            self.config["integration_weights"][f"state_{i}_in1"] = {
                "cosine": np.real(weights[i, :]).tolist(),
                "sine": (-np.imag(weights[i, :])).tolist(),
            }
            self._add_iw_to_all_pulses(f"state_{i}_in1")
            self.config["integration_weights"][f"state_{i}_in2"] = {
                "cosine": np.imag(weights[i, :]).tolist(),
                "sine": np.real(weights[i, :]).tolist(),
            }
            self._add_iw_to_all_pulses(f"state_{i}_in2")

    def _simulation_config(self):
        pass

    def _qua_program(self, **kwargs):
        pass

    @property
    def weights(self) -> dict:

        if self.saved_data and self.finish_train > 0:
            return self.saved_data
        else:
            print("The weights haven't been trained")

    def _downconvert(self, x, ts, simulate=False):

        # calculate the time difference
        if self.time_diff is None:
            td = TimeDiffCalibrator(self.qmm, self.config, self.resonator, reps=1)
            self.time_diff = td.calibrate(simulate=simulate)
            print(
                "The time difference between the modualtion signal and the cos/sin calcualtion over the adc is ",
                self.time_diff,
                "ns",
            )

        # return the signal with exp(j2pif(t-time_diff))
        # NOTE: For the QM example, they use exp(-j2pif(t-time_diff)), it seems that it is suitable for the setting
        # Q = -Q1 + I2
        # For the IR mixer, when we use exp(-j2pif(t-time_diff)), we get best discriminaiton in the axis of Q
        # rather than I axis. Thereby, we use exp(j2pif(t-time_diff)) to get the maximal discrimination in the I axis.

        rr_freq = self._get_qe_freq(self.resonator)
        sig = x * np.exp(1j * 2 * np.pi * rr_freq * 1e-9 * (ts - self.time_diff))

        return sig

    def _get_traces(
        self, qe, correction_method, I_res, Q_res, seq0, sig, use_hann_filter
    ):
        """
        gmm method:
            1. According to the I Q data, it will generate several predicted gaussian distributions for
            different qubit state
            2. ``pr_state`` will get a prediction about which group each IQ pair belongs to. it is a list
            filled by the group index. However it does not correspond to the state index (0:g, 1:e)
            3. ``mapping`` calculate the most group index for each qubit state, indicating the corresponding
            group index for different qubit state(e.g [1, 0])
            4. if the element in ``pr_state`` is the same as the index in the mapping, we will use this trace
            to cacluate the average trace.
        none method:
            1. calcuate the avarage trace for each state
        robust method:
            1. calcuate the median value of the trace for each state
        """

        if correction_method == "gmm":
            data = {"x": I_res, "y": Q_res}
            x = DataFrame(data, columns=["x", "y"])

            gmm = mixture.GaussianMixture(
                n_components=self.num_of_states,
                covariance_type="full",
                tol=1e-12,
                reg_covar=1e-12,
            ).fit(x)

            pr_state = gmm.predict(x)

            mapping = [
                np.argmax(np.bincount(pr_state[seq0 == i]))
                for i in range(self.num_of_states)
            ]

            traces = np.array(
                [
                    np.mean(sig[pr_state == mapping[i], :], axis=0)
                    for i in range(self.num_of_states)
                ]
            )

        elif correction_method == "none" or correction_method == "robust":
            if correction_method == "none":
                traces = np.array(
                    [
                        np.mean(sig[seq0 == i, :], axis=0)
                        for i in range(self.num_of_states)
                    ]
                )

            else:
                traces = np.array(
                    [
                        np.median(np.real(sig[seq0 == i, :]), axis=0)
                        + 1j * np.median(np.imag(sig[seq0 == i, :]), axis=0)
                        for i in range(self.num_of_states)
                    ]
                )

        else:
            raise Exception("unknown correction_method")

        print("------------------------------------------------")
        plt.figure()
        plt.title("Trace of ground state")
        plt.plot(np.abs(traces[0]), label="abs")
        plt.plot(np.real(traces[0]), label="real")
        plt.plot(np.imag(traces[0]), label="imag")
        plt.legend()
        plt.show()

        plt.figure()
        plt.title("Trace of excited state")
        plt.plot(np.abs(traces[1]), label="abs")
        plt.plot(np.real(traces[1]), label="real")
        plt.plot(np.imag(traces[1]), label="imag")
        plt.legend()
        plt.show()

        if use_hann_filter:
            rr_freq = self._get_qe_freq(qe)
            period_ns = int(1 / np.abs(rr_freq) * 1e9)
            hann = signal.hann(period_ns * 2, sym=True)

            hann = hann / np.sum(hann)
            traces = np.array(
                [
                    np.convolve(traces[i, :], hann, "same")
                    for i in range(self.num_of_states)
                ]
            )

        return traces

    @staticmethod
    def _quantize_traces(traces):
        weights = []
        for i in range(traces.shape[0]):
            weights.append(np.average(np.reshape(traces[i, :], (-1, 4)), axis=1))

        return np.array(weights)

    def _execute_and_fetch(self):
        pass

    def train(
        self,
        program=None,
        use_hann_filter=True,
        plot=False,
        reps=None,
        correction_method="robust",
        simulate=False,
        simulation_config=None,
        **execute_args,
    ):
        """
        The train procedure is used to calibrate the optimal weights and bias for each state. A file with the optimal
        parameters is generated during training, and it is used during the subsequent measure_state procedure.
        A training program must be provided in the constructor.

        Args：
        program: a training program. A program that generates training sets. The program should generate equal
        number of training sets for each one of the states. Collection of training sets is achieved by first preparing
        the qubit in one of the states, and then measure the readout resonator element. The measure command must include
        streaming of the raw data (the tag must be called "adc") and the final complex demodulation results must be saved
        under the tags "I" and "Q".

        use_hann_filter: Whether or not to use a LPF on the averaged sampled baseband waveforms.
        plot: Whether or not to plot some figures for debug purposes.
        """
        if reps is not None:
            self.N = reps

        if program is None:
            program = self._qua_program(simulate=simulate, use_opt_weights=False)

        if simulate and simulation_config is None:
            simulation_config = self._simulation_config()

        results = self._execute_and_fetch(
            program, simulation_config=simulation_config, **execute_args
        )

        I_res, Q_res, ts, x = results[0], results[1], results[2], results[3]
        measures_per_state = len(I_res) // self.num_of_states

        # seq0 is 1-dimentional array [0,0...,1,1,...,2,2,...]
        # representing the expected state
        seq0 = np.array(
            [[i] * measures_per_state for i in range(self.num_of_states)]
        ).flatten()

        # x is the adc signal whose length is the readout pulse + 2*smearing we need to omit the smearing part
        if self.smearing != 0:
            x_demod = x[:, self.smearing : -self.smearing]
            ts_demod = ts[:, self.smearing : -self.smearing]
        else:
            x_demod = x
            ts_demod = ts

        # sig is the downconversion of the signal
        sig = self._downconvert(x_demod, ts_demod, simulate=simulate)

        traces = self._get_traces(
            self.resonator, correction_method, I_res, Q_res, seq0, sig, use_hann_filter
        )
        weights = self._quantize_traces(traces)

        # normalization
        # ``norm`` is the maximal absolute value of the weights
        norm = np.max(np.abs(weights))
        weights = weights / norm

        # The square of Frobenius norm of the raw weights

        bias = (np.linalg.norm(weights * norm, axis=1) ** 2) / norm / 2 * (2 ** -24) * 4

        # save weights
        np.savez(self.path, weights=weights, bias=bias)
        self.saved_data = {"weights": weights, "bias": bias}
        self.finish_train = 1

        # update configuration
        self._update_config()

        # plot raw I Q and weights
        if plot:
            self.plot(I_res=I_res, Q_res=Q_res, seq0=seq0, weights=weights)

    def plot(self, I_res, Q_res, seq0, weights):
        plt.figure()
        plt.title("The IQ for different qubit states")
        for i in range(self.num_of_states):
            I_ = I_res[seq0 == i]
            Q_ = Q_res[seq0 == i]
            plt.plot(I_, Q_, ".", label=f"state {i}")
            plt.axis("equal")
        plt.xlabel("I")
        plt.ylabel("Q")
        plt.legend()

        plt.figure()
        for i in range(self.num_of_states):
            plt.subplot(self.num_of_states, 1, i + 1)
            plt.title(f"The weights of state {i}")
            plt.tight_layout()
            plt.plot(np.real(weights[i, :]), label=f"Re[weights] of state {i}")
            plt.plot(np.imag(weights[i, :]), label=f"Imag[weights] of state {i}")

        plt.figure()
        for i in range(self.num_of_states):
            plt.subplot(self.num_of_states, 1, i + 1)
            plt.tight_layout()
            plt.title(f"The complex weights of state {i}")
            plt.plot(np.real(weights[i, :]), np.imag(weights[i, :]))
            plt.axis("equal")
