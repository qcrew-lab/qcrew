import numpy as np
from pandas import DataFrame
from sklearn import mixture
from scipy import signal
import scipy.fftpack
import seaborn as sns

import matplotlib.pyplot as plt


class StateDiscriminator:
    def __init__(
        self,
        resonator: str,
        config: dict,
        time_diff: int = None,
        num_of_states: int = 2,
    ):

        self.config = config
        self.resonator = resonator
        self.int_freq = self.config["elements"][resonator]["intermediate_frequency"]
        self.smearing = self.config["elements"][resonator]["smearing"]
        self.num_of_states = num_of_states
        self.time_diff = time_diff

        self.time_diff = 36
        self.measures_per_state = None
        self.adc = None
        self.ts = None
        self.I = None
        self.Q = None
        self.res = None
        self.state_seq = None
        self.envelopes = None

    def get_envelopes(
        self,
        adc: np.ndarray,
        ts: np.ndarray,
        I: np.ndarray = None,
        Q: np.ndarray = None,
        method: str = "none",
        use_hann_filter: bool = True,
    ) -> np.ndarray:

        ############################################
        # get data
        self.adc = adc
        self.ts = ts
        self.I = I
        self.Q = Q

        ############################################
        # get parameters
        self.measures_per_state = len(adc) // self.num_of_states
        self.state_seq = np.array(
            [[i] * self.measures_per_state for i in range(self.num_of_states)]
        ).flatten()

        if self.smearing != 0:
            adc = adc[:, self.smearing : -self.smearing]
            ts = ts[:, self.smearing : -self.smearing]

        ############################################
        # downconvert
        # return the signal with exp(j2pif(t-time_diff))
        # NOTE: For the QM example, they use exp(-j2pif(t-time_diff)), it seems that it is suitable for the setting
        # Q = -Q1 + I2
        # For the IR mixer, when we use exp(-j2pif(t-time_diff)), we get best discriminaiton in the axis of Q
        # rather than I axis. Thereby, we use exp(j2pif(t-time_diff)) to get the maximal discrimination in the I axis.

        n_datapoints = adc.shape[1]
        t_rel = np.linspace(0, n_datapoints - 1, n_datapoints)
        sig = adc * np.exp(
            1j * 2 * np.pi * self.int_freq * 1e-9 * t_rel  # (ts)  # - self.time_diff)
        )

        ############################################
        # averaging
        if method == "none":
            avg_trace = np.array(
                [
                    np.mean(sig[self.state_seq == i, :], axis=0)
                    for i in range(self.num_of_states)
                ]
            )
        elif method == "gmm":
            if I is not None and Q is not None:
                data = {"x": I, "y": Q}
                x = DataFrame(data, columns=["x", "y"])

                gmm = mixture.GaussianMixture(
                    n_components=self.num_of_states,
                    covariance_type="full",
                    tol=1e-12,
                    reg_covar=1e-12,
                ).fit(x)

                pr_state = gmm.predict(x)
                mapping = [
                    np.argmax(np.bincount(pr_state[self.state_seq == i]))
                    for i in range(self.num_of_states)
                ]

                avg_trace = np.array(
                    [
                        np.mean(sig[pr_state == mapping[i], :], axis=0)
                        for i in range(self.num_of_states)
                    ]
                )
            else:
                raise ValueError("I and Q are not given.")

        elif method == "median":
            avg_trace = np.array(
                [
                    np.median(np.real(sig[self.state_seq == i, :]), axis=0)
                    + 1j * np.median(np.imag(sig[self.state_seq == i, :]), axis=0)
                    for i in range(self.num_of_states)
                ]
            )
        else:
            raise Exception("unknown averaging method")

        ############################################
        # Hann filter

        if use_hann_filter:
            period_ns = int(1 / np.abs(self.int_freq) * 1e9)
            hann = signal.hann(period_ns * 2, sym=True)

            hann = hann / np.sum(hann)
            env = np.array(
                [
                    np.convolve(avg_trace[i, :], hann, "same")
                    for i in range(self.num_of_states)
                ]
            )
        else:
            env = avg_trace

        self.envelopes = env

        return env

    def get_weights_threshold(self, envelope: np.ndarray) -> tuple:

        ############################################
        # normalization and threshold
        norm = np.max(np.abs(envelope))
        envelope = envelope / norm
        print(envelope.shape)
        bias = (
            (np.linalg.norm(envelope * norm, axis=1) ** 2) / norm / 2 * (2 ** -24) * 4
        )
        print(bias)
        threshold = bias[0] - bias[1]

        ############################################
        # quantization
        squeezed_envelope = []
        for i in range(envelope.shape[0]):
            squeezed_envelope.append(
                np.average(np.reshape(envelope[i, :], (-1, 4)), axis=1)
            )
        raw_weights = np.array(squeezed_envelope)
        print(raw_weights.shape)

        weights = {}
        # b_vec = -1 * (raw_weights[0, :] - raw_weights[1, :]).conj()
        b_vec = (raw_weights[0, :] - raw_weights[1, :]).conj()
        weights["I"] = np.array([np.real(b_vec).tolist(), (-np.imag(b_vec)).tolist()])
        weights["Q"] = np.array([np.imag(b_vec).tolist(), np.real(b_vec).tolist()])
        
        return weights, threshold

    @staticmethod
    def plot(
        data: np.ndarray, title: str, xlabel: str = "time", ylabel: str = "signal"
    ) -> None:
        length = len(data)

        plt.figure()
        ax = plt.subplot()
        ax.set_title(title + " length:{}".format(length))
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.plot(np.real(data), label="Real")
        ax.plot(np.imag(data), label="Imag")
        plt.legend()
        plt.tight_layout()
        plt.show()

    @staticmethod
    def fft_plot(data: np.ndarray, title: str) -> None:

        N = len(data)
        T = float(1e-9)
        yf = scipy.fftpack.fft(data)
        xf = np.linspace(0.0, 1.0 / (2.0 * T), N // 2) * 1e-6

        fig, axes = plt.subplots(2, 1)
        axes[0].set_title(title + " length:{}".format(N))
        axes[0].set_xlabel("time")
        axes[0].plot(data)
        axes[1].set_title("fft")
        axes[1].plot(xf, 2.0 / N * np.abs(yf[: N // 2]))
        axes[1].set_xlabel("Hz")
        fig.tight_layout()
        plt.show()


def histogram_plot(I, Q, state_seq, num_of_states, threshold):

    plt.figure()
    plt.title("The IQ for different qubit states")
    for i in range(num_of_states):
        I_ = I[state_seq == i]
        Q_ = Q[state_seq == i]
        plt.plot(I_, Q_, ".", label=f"state {i}")

    plt.axis("equal")
    plt.xlabel("I")
    plt.ylabel("Q")
    plt.legend()

    plt.figure()
    plt.title("The discrimination of the states by I Q")
    for i in range(num_of_states):
        plt.hist(I[np.array(state_seq) == i], 50, label=f"state {i}")
    plt.plot([threshold] * 2, [0, num_of_states / 100], "g")
    plt.legend()
    plt.show()


def fidelity_plot(res, state_seq):
    p_s = np.zeros(shape=(2, 2))
    for i in range(2):
        res_i = res[np.array(state_seq) == i]
        p_s[i, :] = np.array([np.mean(res_i == 0), np.mean(res_i == 1)])
    labels = ["g", "e"]

    plt.figure()
    ax = plt.subplot()
    sns.heatmap(p_s, annot=True, ax=ax, fmt="g", cmap="Blues")

    ax.set_xlabel("Predicted labels")
    ax.set_ylabel("Prepared labels")
    ax.set_title("Confusion Matrix")
    ax.xaxis.set_ticklabels(labels)
    ax.yaxis.set_ticklabels(labels)
    plt.show()
