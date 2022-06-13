""" """

import math
import time
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize

import qcrew.control.instruments.qm as qciqm
from qcrew.control.instruments.signal_hound.sa124 import Sa124
import qcrew.control.modes as qcm
from qcrew.helpers import logger, minimizer

from qm import _Program
from qm.QmJob import QmJob
from qm.qua import infinite_loop_, program
from qm.QuantumMachine import QuantumMachine


class MixerTuner:
    """
    Use tune_lo or tune_sb to minimize local oscillator leakage and upper sideband leakage respectively. Both methods require the mode object as well as a method key - either "BF" (default) to run Brute-Force minimizer or "NM" to run Nelder-Mead minimizer. The BF minimizer allows more control over the minimization but is slower. The NM minimizer is faster but its inner workings cannot be finely controlled.

    Note that the BF minimizer is minimizing the amplitude level whereas the NM minimizer is minimizing the contrast between signal peak and floor (to lower than the 3dB threshold).
    """

    # parameters common to both Nelder-Mead and Brute-Force minimization
    threshold: float = 3.0  # in dBm
    ref_power: float = 0.0

    # Nelder-Mead (NM) parameters
    simplex: np.ndarray = np.array([[0.0, 0.0], [0.0, 0.1], [0.1, 0.0]])
    maxiter: int = 100
    span: float = 2e6
    rbw: float = 50e3

    def __init__(self, sa: Sa124, qm: QuantumMachine) -> None:
        """ """
        self._sa: Sa124 = sa
        self._qm: QuantumMachine = qm

        self._qm_job = None  # will be set and halted by the tune methods
        self._initial_contrast = None  # set during tuning check

    def tune_lo(self, mode, method: str = "BF", **kwargs):
        """ """
        self._setup(mode)
        # these three return values are only needed for NM, BF sets them to None
        is_tuned, center_idx, floor = self._check_tuning(mode, method, "LO")
        i_offset, q_offset = None, None

        if method == "BF":
            i_offset, q_offset = self._tune_lo_bf(mode, **kwargs)
        elif method == "NM":
            if is_tuned:
                logger.success("LO already tuned to within {self.threshold}dBm!")
                return
            i_offset, q_offset = self._tune_lo_nm(mode, center_idx, floor)

        if i_offset is not None and q_offset is not None:
            mode.mixer_offsets = {"I": i_offset, "Q": q_offset}

        self._qm_job.halt()

    def tune_sb(self, mode, method: str = "BF", **kwargs):
        """ """
        self._setup(mode)
        # these three return values are only needed for NM, BF sets them to None
        is_tuned, center_idx, floor = self._check_tuning(mode, method, "SB")
        g_offset, p_offset = None, None

        if method == "BF":
            g_offset, p_offset = self._tune_sb_bf(mode, **kwargs)
        elif method == "NM":
            if is_tuned:
                logger.success("SB already tuned to within {self.threshold}dBm!")
                return
            g_offset, p_offset = self._tune_sb_nm(mode, center_idx, floor)

        if g_offset is not None and p_offset is not None:
            mode.mixer_offsets = {"G": g_offset, "P": p_offset}
            c_matrix = qciqm.QMConfig.get_mixer_correction_matrix(g_offset, p_offset)
            logger.info(f"Final mixer correction matrix: {c_matrix}")

        self._qm_job.halt()

    def _setup(self, mode):
        """Play carrier frequency and intermediate frequency to mode and check current tuning"""
        try:
            mode.lo.rf = True
        except AttributeError:
            logger.error(f"{mode} is not a Mode object, please run with a Mode object")
            raise
        else:
            self._qm_job = self._qm.execute(self._get_qua_program(mode))

    def _check_tuning(self, mode, method, key):
        """ """
        center = mode.lo_freq if key == "LO" else mode.lo_freq - mode.int_freq
        if method == "BF":
            amp = self._sa.single_sweep(
                center=center, verify_freq=True, set_zeroif_params=True
            )
            logger.info(f"Initial amp of {key} leakage: {amp}")
            return None, None, None  # dummy values, they don't matter
        elif method == "NM":
            span, rbw, ref_pow = self.span, self.rbw, self.ref_power
            fs, amps = self._sa.sweep(
                center=center, span=span, rbw=rbw, ref_power=ref_pow
            )
            sweep_info = self._sa.sweep_info
            center_idx = math.ceil(sweep_info["sweep_length"] / 2 + 1)
            stop, start = int(center_idx / 2), int(center_idx + (center_idx / 2))
            floor = (np.average(amps[:stop]) + np.average(amps[start:])) / 2
            contrast = amps[center_idx] - floor
            is_tuned = contrast < self.threshold
            real_center = fs[center_idx]
            logger.info(f"Tune check at {real_center:7E}: {contrast = :.5}dBm")
            self._initial_contrast = contrast
            return is_tuned, center_idx, floor
        else:
            raise ValueError(f"{method = } is not a valid key, use 'BF' or 'NM'")

    def _tune_lo_bf(self, mode, offset_range, **kwargs):
        """ """
        range0, range1 = offset_range

        def objective_fn(params):
            i_offset, q_offset = params["I"].value, params["Q"].value
            self._qm.set_output_dc_offset_by_element(mode.name, "I", i_offset)
            self._qm.set_output_dc_offset_by_element(mode.name, "Q", q_offset)
            val = self._sa.single_sweep()
            logger.info(f"Measuring at I: {i_offset}, Q: {q_offset}, amp: {val}")
            return val

        i_offset, q_offset = mode.mixer_offsets["I"], mode.mixer_offsets["Q"]
        opt_params = self._minimize_bf(
            objective_fn, ("I", "Q"), i_offset, q_offset, range0, range1, **kwargs
        )
        return opt_params["I"].value, opt_params["Q"].value

    def _tune_lo_nm(self, mode, center_idx, floor):
        """ """
        logger.info(f"Minimizing {mode} LO leakage...")

        def objective_fn(offsets: tuple[float]) -> float:
            i_offset, q_offset, mode_name = offsets[0], offsets[1], mode.name
            self._qm.set_output_dc_offset_by_element(mode_name, "I", i_offset)
            self._qm.set_output_dc_offset_by_element(mode_name, "Q", q_offset)
            contrast = self._get_contrast(center_idx, floor)
            logger.debug(f"Set I: {i_offset}, Q: {q_offset}. {contrast = }")
            return contrast

        result = self._minimize_nm(objective_fn, bounds=((-0.5, 0.5), (-0.5, 0.5)))
        return result if result is not None else (None, None)

    def _tune_sb_bf(self, mode, offset_range, **kwargs):
        """ """
        range0, range1 = offset_range

        def objective_fn(params):
            g_offset, p_offset = params["G"].value, params["P"].value
            correction_matrix = qciqm.QMConfig.get_mixer_correction_matrix(
                g_offset, p_offset
            )
            self._qm_job.set_element_correction(mode.name, correction_matrix)
            val = self._sa.single_sweep()
            logger.info(f"Measuring at G: {g_offset}, P: {p_offset}, amp: {val}")
            return val

        g_offset, p_offset = mode.mixer_offsets["G"], mode.mixer_offsets["P"]
        opt_params = self._minimize_bf(
            objective_fn, ("G", "P"), g_offset, p_offset, range0, range1, **kwargs
        )
        return opt_params["G"].value, opt_params["P"].value

    def _tune_sb_nm(self, mode, center_idx, floor):
        """ """
        logger.info(f"Minimizing {mode} SB leakage...")

        def objective_fn(offsets: tuple[float]) -> float:
            c_matrix = qciqm.QMConfig.get_mixer_correction_matrix(*offsets)
            if any(x < -2 or x > 2 for x in c_matrix):
                logger.info("Found out of bounds value in c-matrix")
                return self._initial_contrast
            self._qm_job.set_element_correction(mode.name, c_matrix)
            contrast = self._get_contrast(center_idx, floor)
            logger.debug(f"Set G: {offsets[0]}, P: {offsets[1]}. {contrast = }")
            return contrast

        result = self._minimize_nm(objective_fn, bounds=None)
        return result if result is not None else (None, None)

    def _minimize_bf(
        self,
        func,
        param_names,
        init0,
        init1,
        range0,
        range1,
        num_iterations=4,
        num_points=11,
        range_divider=4,
        plot=False,
        verbose=False,
    ):
        p0, p1 = param_names
        m = minimizer.Minimizer(
            func,
            n_it=num_iterations,
            n_eval=num_points,
            range_div=range_divider,
            verbose=verbose,
            plot=plot,
        )
        m.add_parameter(minimizer.Parameter(p0, value=float(init0), vrange=range0))
        m.add_parameter(minimizer.Parameter(p1, value=float(init1), vrange=range1))
        m.minimize()
        return m.params

    def _minimize_nm(
        self,
        fn: Callable[[tuple[float]], float],
        bounds,
    ) -> tuple[float]:
        """ """
        start_time = time.perf_counter()
        opt = {
            "fatol": self.threshold,
            "initial_simplex": self.simplex,
            "maxiter": self.maxiter,
        }
        result = scipy.optimize.minimize(
            fn, [0, 0], method="Nelder-Mead", bounds=bounds, options=opt
        )
        if result.success:
            time_, contrast = time.perf_counter() - start_time, fn(result.x)
            logger.success(f"Minimized in {time_:.5}s with final {contrast = :.5}")
            if contrast > self.threshold:
                diff = contrast - self.threshold
                logger.warning(f"Final contrast exceeds threshold by {diff}dBm")
            return result.x
        else:
            logger.error(f"Minimization unsuccessful, details: {result.message}")

    def _get_qua_program(self, mode: qcm.Mode) -> _Program:
        """ """
        with program() as mixer_tuning:
            with infinite_loop_():
                mode.play("constant_pulse")
        return mixer_tuning

    def _get_contrast(self, center_idx: int, floor: float) -> float:
        """ """
        _, amps = self._sa.sweep()
        return abs(amps[center_idx] - floor)

    def landscape(self, mode, key, xlim, ylim, points):
        """
        mode: the mode object
        key: string "LO" or " SB"
        xlim: tuple (min, max) for the landscape x axis
        ylim: tuple (min, max) for the landscape y axis
        points: number of points to sweep for x and y
        """
        # create landscape grid
        x = np.linspace(*xlim, points)
        y = np.linspace(*ylim, points)
        xx, yy = np.meshgrid(x, y)
        zz = np.zeros((points, points))

        mode.lo.rf = True  # play carrier freq to mode
        job = self._qm.execute(self._get_qua_program(mode))  # play int freq

        # prepare SA for fast sweeps and prepare the objective functions
        func, center_idx = None, None
        if key == "LO":
            center = mode.lo_freq
            # do this to set the SA
            self._sa.sweep(
                center=center, span=self.span, rbw=self.rbw, ref_power=self.ref_power
            )
            sweep_info = self._sa.sweep_info
            center_idx = math.ceil(sweep_info["sweep_length"] / 2 + 1)

            def lo_fn(offsets: tuple[float]) -> float:
                self._qm.set_output_dc_offset_by_element(mode.name, "I", offsets[0])
                self._qm.set_output_dc_offset_by_element(mode.name, "Q", offsets[1])
                _, amps = self._sa.sweep()
                return amps[center_idx]

            func = lo_fn

        elif key == "SB":
            center = mode.lo_freq - mode.int_freq  # upper sideband to suppress
            # do this to set the SA
            self._sa.sweep(
                center=center, span=self.span, rbw=self.rbw, ref_power=self.ref_pow
            )
            sweep_info = self._sa.sweep_info
            center_idx = math.ceil(sweep_info["sweep_length"] / 2 + 1)

            def sb_fn(offsets: tuple[float]) -> float:
                c_matrix = qciqm.QMConfig.get_mixer_correction_matrix(*offsets)
                job.set_element_correction(mode.name, c_matrix)
                _, amps = self._sa.sweep()
                return amps[center_idx]

            func = sb_fn

        logger.info(f"Finding {key} landscape for '{mode}'...")

        # evaluate the objective functions on the grid
        for i in range(points):
            for j in range(points):
                zz[i][j] = func((xx[i][j], yy[i][j]))
                logger.info(f"Set: {xx[i][j]}, {yy[i][j]}. Get {zz[i][j]}")

        # show final plot
        plt.pcolormesh(x, y, zz, shading="auto", cmap="viridis")
        plt.colorbar()
