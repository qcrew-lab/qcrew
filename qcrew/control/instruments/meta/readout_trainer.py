""" """

import numpy as np
from scipy import signal

import qcrew.control.modes as qcm
import qcrew.control.pulses as qcp
from qcrew.analyze import fit
import qcrew.measure.qua_macros as macros

# from qcrew.control.pulses import integration_weights
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized

from typing import ClassVar
import matplotlib.pyplot as plt
from qm import _Program
from qm import qua

ADC_TO_VOLTS = 2 ** -12
TS = 1e-9  # Sampling time of the OPX in seconds
T_OFS = 35.96


class ReadoutTrainer(Parametrized):
    """ """

    _parameters: ClassVar[set[str]] = {
        "mode_names",  # names of the modes used in the experiment
        "reps",  # number of times the experiment is repeated
        "wait_time",  # wait time between fetching and plotting
        "qubit_pi_pulse",
    }

    def __init__(
        self,
        rr: qcm.Mode,
        qubit: qcm.Mode,
        qm,
        reps,
        wait_time,
        qubit_pi_pulse,
        ddrop_params={},
        weights_file_path=None,
    ):
        """ """
        self._rr: qcm.Mode = rr
        self._qubit: qcm.Mode = qubit
        self._qm = qm
        self.modes = [rr, qubit]
        self.mode_names = [mode.name for mode in self.modes]
        self.reps = reps
        self.wait_time = wait_time
        self.qubit_pi_pulse = qubit_pi_pulse
        self.ddrop_params = ddrop_params
        self.weights_file_path = weights_file_path
        # get qubit ef mode from ddrop params dictionary
        self._qubit_ef = None
        if "qubit_ef_mode" in self.ddrop_params.keys():
            self._qubit_ef = self.ddrop_params["qubit_ef_mode"]
            del self.ddrop_params["qubit_ef_mode"]

        logger.info(f"Initialized ReadoutTrainer with {self._rr} and {self._qubit}")

    def train_weights(self) -> None:
        """
        Obtain integration weights of rr given the excited and ground states of qubit and update rr mode.
        """

        # Start with constant integration weights. Not really necessary
        # self._reset_weights()

        # Get traces and average envelope when qubit in ground state
        trace_g_list, timestamps_g = self._acquire_traces(self._qm, excite_qubit=False)
        env_g = self._calc_average_envelope(trace_g_list, timestamps_g, T_OFS)

        # Get traces and average envelope when qubit in excited state
        trace_e_list, timestamps_e = self._acquire_traces(self._qm, excite_qubit=True)
        env_e = self._calc_average_envelope(trace_e_list, timestamps_e, T_OFS)

        # Get difference between average envelopes
        envelope_diff = env_g - env_e

        # Normalize and squeeze by 1/4th
        norm = np.max(np.abs(envelope_diff))
        norm_envelope_diff = envelope_diff / norm
        squeezed_diff = self._squeeze_array(norm_envelope_diff)  # convert shape

        # Update readout with optimal weights
        weights = self._update_weights(squeezed_diff)

        # Plot envelopes
        fig, axes = plt.subplots(2, 1, sharex=True, figsize=(7, 10))
        axes[0].plot(1000 * np.real(env_g), label="Re")
        axes[0].plot(1000 * np.imag(env_g), label="Imag")
        axes[0].set_title("|g> envelope")
        axes[0].set_ylabel("Amplitude (mV)")
        axes[0].legend()
        axes[1].plot(1000 * np.real(env_e))
        axes[1].plot(1000 * np.imag(env_e))
        axes[1].set_title("|e> envelope")
        axes[1].set_ylabel("Amplitude (mV)")
        axes[1].set_xlabel("Time (ns)")
        plt.show()

        return env_g, env_e

    def _reset_weights(self):
        """
        Start the pulse with constant integration weights
        """
        integration_weights = qcp.OptimizedIntegrationWeights(
            length=int(self._rr.readout_pulse.length / 4)
        )
        self._rr.readout_pulse.integration_weights = integration_weights

    def _acquire_traces(self, qm, excite_qubit: bool = False) -> tuple[list]:
        """
        Run QUA program to obtain traces of the readout pulse.
        """

        # Execute script
        qua_program = self._get_QUA_trace_acquisition(excite_qubit)
        job = self._qm.execute(qua_program)

        handle = job.result_handles
        handle.wait_for_all_values()
        timestamps = handle.get("timestamps").fetch_all()["value"]
        adc = handle.get("adc").fetch_all()["value"]

        return ADC_TO_VOLTS * adc, timestamps

    def _get_QUA_trace_acquisition(self, excite_qubit: bool = False) -> _Program:
        """ """
        reps = self.reps
        wait_time = self.wait_time
        readout_pulse = "readout_pulse"
        qubit_pi_pulse = self.qubit_pi_pulse

        with qua.program() as acquire_traces:
            adc = qua.declare_stream(adc_trace=True)
            n = qua.declare(int)

            with qua.for_(n, 0, n < reps, n + 1):

                if self.ddrop_params:
                    macros.DDROP_reset(
                        self._qubit,
                        self._rr,
                        **self.ddrop_params,
                        qubit_ef=self._qubit_ef,
                    )

                qua.measure(readout_pulse, self._rr.name, adc)
                qua.wait(wait_time)
                # qua.reset_phase(self._rr.name)

                if self.ddrop_params:
                    macros.DDROP_reset(
                        self._qubit,
                        self._rr,
                        **self.ddrop_params,
                        qubit_ef=self._qubit_ef,
                    )

                if excite_qubit:
                    qua.align(self._rr.name, self._qubit.name)
                    self._qubit.play(qubit_pi_pulse)
                    qua.align(self._rr.name, self._qubit.name)

                qua.measure(readout_pulse, self._rr.name, adc)
                qua.wait(wait_time)

            with qua.stream_processing():
                # streams for envelope calculation
                adc.input1().timestamps().save_all("timestamps")
                adc.input1().save_all("adc")

                # streams for plotting/bug fixing
                adc.input1().average().save("adc_avg")
                adc.input1().average().fft().save("adc_fft")

        return acquire_traces

    def _calc_average_envelope(self, trace_list, timestamps, t_ofs):
        int_freq = np.abs(self._rr.int_freq)

        # demodulate
        s = trace_list * np.exp(1j * 2 * np.pi * int_freq * TS * (timestamps - t_ofs))

        # filter 2*omega_IF using hann filter
        hann = signal.hann(int(2 / TS / int_freq), sym=True)
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

    def _update_weights(self, squeezed_diff):

        weights = {}
        weights["I"] = np.array(
            [np.real(squeezed_diff).tolist(), (np.imag(squeezed_diff)).tolist()]
        )
        weights["Q"] = np.array(
            [np.imag(-squeezed_diff).tolist(), np.real(squeezed_diff).tolist()]
        )

        path = self.weights_file_path

        # Save weights to npz file
        np.savez(path, **weights)

        # Update the readout pulse with the npz file path
        self._rr.readout_pulse.integration_weights(path=path)

        return weights

    def calculate_threshold(self):

        # Get IQ for qubit in ground state
        IQ_acquisition_program = self._get_QUA_IQ_acquisition()
        job = self._qm.execute(IQ_acquisition_program)
        handle = job.result_handles
        handle.wait_for_all_values()
        Ig_list = handle.get("I").fetch_all()["value"]
        Qg_list = handle.get("Q").fetch_all()["value"]

        # Get IQ for qubit in excited state
        IQ_acquisition_program = self._get_QUA_IQ_acquisition(excite_qubit=True)
        job = self._qm.execute(IQ_acquisition_program)
        handle = job.result_handles
        handle.wait_for_all_values()
        Ie_list = handle.get("I").fetch_all()["value"]
        Qe_list = handle.get("Q").fetch_all()["value"]

        # Fit each blob to a 2D gaussian and retrieve the center
        IQ_center_g, data_g = self._fit_IQ_blob(Ig_list, Qg_list)
        IQ_center_e, data_e = self._fit_IQ_blob(Ie_list, Qe_list)

        # Calculate threshold
        threshold = (IQ_center_g[0] + IQ_center_e[0]) / 2

        # Plot scatter and contour of each blob
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.set_aspect("equal")
        ax.scatter(Ig_list, Qg_list, label="|g>", s=5)
        ax.scatter(Ie_list, Qe_list, label="|e>", s=5)
        ax.contour(
            data_g["I_grid"],
            data_g["Q_grid"],
            data_g["counts_fit"],
            levels=5,
            cmap="winter",
        )
        ax.contour(
            data_e["I_grid"],
            data_e["Q_grid"],
            data_e["counts_fit"],
            levels=5,
            cmap="autumn",
        )
        ax.plot(
            [threshold, threshold],
            [np.min(data_g["Q_grid"]), np.max(data_g["Q_grid"])],
            label="threshold",
            c="k",
            linestyle="--",
        )

        ax.set_title("IQ blobs for each qubit state")
        ax.set_ylabel("Q")
        ax.set_xlabel("I")
        ax.legend()
        plt.show()

        # Plot I histogram
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(Ig_list, bins=50)
        ax.hist(Ie_list, bins=50)

        ax.set_title("Projection of the IQ blobs onto the I axis")
        ax.set_ylabel("counts")
        ax.set_xlabel("I")
        ax.legend()
        plt.show()

        # Update readout with optimal threshold
        self._update_threshold(threshold)

        # Calculates the confusion matrix of the readout
        self._calculate_confusion_matrix(Ig_list, Ie_list, threshold)

        # Organize the raw I and Q data for each G and E measurement
        data = {
            "Ig": Ig_list,
            "Qg": Qg_list,
            "Ie": Ie_list,
            "Qe": Qe_list,
        }

        return threshold, data

    def _fit_IQ_blob(self, I_list, Q_list):

        fit_fn = "gaussian2d_symmetric"

        # Make ground IQ blob in a 2D histogram
        zs, xs, ys = np.histogram2d(I_list, Q_list, bins=50)

        # Replace "bin edge" by "bin center"
        dx = xs[1] - xs[0]
        xs = (xs - dx / 2)[1:]
        dy = ys[1] - ys[0]
        ys = (ys - dy / 2)[1:]

        # Get fit to 2D gaussian
        xs_grid, ys_grid = np.meshgrid(xs, ys)
        params = fit.do_fit(fit_fn, xs_grid.T, ys_grid.T, zs=zs)
        IQ_center = (params["x0"], params["y0"])  # gaussian center
        fit_zs = fit.eval_fit(fit_fn, params, xs_grid.T, ys_grid.T).T

        data = {
            "I_grid": xs_grid,
            "Q_grid": ys_grid,
            "counts": zs,
            "counts_fit": fit_zs,
        }

        return IQ_center, data

    def _get_QUA_IQ_acquisition(self, excite_qubit: bool = False):
        """ """
        reps = self.reps
        wait_time = self.wait_time
        qubit_pi_pulse = self.qubit_pi_pulse

        with qua.program() as acquire_IQ:
            I = qua.declare(qua.fixed)
            Q = qua.declare(qua.fixed)
            n = qua.declare(int)

            with qua.for_(n, 0, n < reps, n + 1):

                if self.ddrop_params:
                    macros.DDROP_reset(
                        self._qubit,
                        self._rr,
                        **self.ddrop_params,
                        qubit_ef=self._qubit_ef,
                    )

                if excite_qubit:
                    qua.align(self._rr.name, self._qubit.name)
                    self._qubit.play(qubit_pi_pulse)
                    qua.align(self._rr.name, self._qubit.name)

                self._rr.measure((I, Q))
                qua.save(I, "I")
                qua.save(Q, "Q")
                qua.wait(wait_time, self._rr.name)

        return acquire_IQ

    def _update_threshold(self, threshold):
        self._rr.readout_pulse.threshold = threshold

    def _calculate_confusion_matrix(self, Ig_list, Ie_list, threshold):
        pgg = 100 * round((np.sum(Ig_list > threshold) / len(Ig_list)), 3)
        pge = 100 * round((np.sum(Ig_list < threshold) / len(Ig_list)), 3)
        pee = 100 * round((np.sum(Ie_list < threshold) / len(Ie_list)), 3)
        peg = 100 * round((np.sum(Ie_list > threshold) / len(Ie_list)), 3)
        print("\nState prepared in |g>")
        print(f"   Measured in |g>: {pgg}%")
        print(f"   Measured in |e>: {pge}%")
        print("State prepared in |e>")
        print(f"   Measured in |e>: {pee}%")
        print(f"   Measured in |g>: {peg}%")
