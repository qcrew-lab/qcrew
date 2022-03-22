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
from qcrew.helpers import logger

from qm import _Program
from qm.QmJob import QmJob
from qm.qua import infinite_loop_, program
from qm.QuantumMachine import QuantumMachine


class MixerTuner:
    """ """

    simplex: np.ndarray = np.array([[0.0, 0.0], [0.0, 0.1], [0.1, 0.0]])
    threshold: float = 2.0  # in dBm
    maxiter: int = 100
    span: float = 2e6
    rbw: float = 50e3
    ref_power: float = 0.0

    def __init__(self, *modes: qcm.Mode, sa: Sa124, qm: QuantumMachine) -> None:
        """ """
        self._sa: Sa124 = sa
        self._qm: QuantumMachine = qm
        self._modes: tuple[qcm.Mode] = modes
        logger.info(f"Initialized MixerTuner with {self._modes}")

    def tune(self) -> None:
        """ """
        try:
            for mode in self._modes:
                mode.lo_freq = mode.lo_freq  # play carrier freq to mode
                job = self._qm.execute(self._get_qua_program(mode))  # play int freq
                self._tune_mode(mode, job)
        except AttributeError:
            logger.error("MixerTuner is initialized with unrecognized arguments")
            raise
        else:
            job.halt()

    def _tune_mode(self, mode: qcm.Mode, job: QmJob) -> None:
        """ """
        for key in ("LO", "SB"):
            center = mode.lo_freq if key == "LO" else mode.lo_freq - mode.int_freq
            is_tuned, center_idx, floor = self._check_tuning(center=center)
            if is_tuned:
                logger.success(f"{key} already tuned to within {self.threshold}dBm!")
                continue
            logger.info(f"Minimizing {mode} {key} leakage...")
            if key == "LO":
                i_offset, q_offset = self._tune_lo(mode, center_idx, floor)
                if i_offset is not None and q_offset is not None:
                    mode.mixer_offsets = {"I": i_offset, "Q": q_offset}
            elif key == "SB":
                g_offset, p_offset = self._tune_sb(mode, job, center_idx, floor)
                if g_offset is not None and p_offset is not None:
                    mode.mixer_offsets = {"G": g_offset, "P": p_offset}

    def _tune_lo(self, mode: qcm.Mode, center_idx: int, floor: float) -> tuple[float]:
        """ """

        def objective_fn(offsets: tuple[float]) -> float:
            i_offset, q_offset, mode_name = offsets[0], offsets[1], mode.name
            self._qm.set_output_dc_offset_by_element(mode_name, "I", i_offset)
            self._qm.set_output_dc_offset_by_element(mode_name, "Q", q_offset)
            contrast = self._get_contrast(center_idx, floor)
            logger.info(f"Set I: {i_offset}, Q: {q_offset}. {contrast = }")
            return contrast

        result = self._minimize(objective_fn)
        return result if result is not None else (None, None)

    def _tune_sb(
        self, mode: qcm.Mode, job: QmJob, center_idx: int, floor: float
    ) -> None:
        """ """

        def objective_fn(offsets: tuple[float]) -> float:
            correction_matrix = qciqm.QMConfig.get_mixer_correction_matrix(*offsets)
            job.set_element_correction(mode.name, correction_matrix)
            contrast = self._get_contrast(center_idx, floor)
            logger.info(f"Set G: {offsets[0]}, P: {offsets[1]}. {contrast = }")
            return contrast

        result = self._minimize(objective_fn)
        return result if result is not None else (None, None)

    def _check_tuning(self, center: float) -> tuple[bool, int, float]:
        """ """
        span, rbw, ref_pow = self.span, self.rbw, self.ref_power
        fs, amps = self._sa.sweep(center=center, span=span, rbw=rbw, ref_power=ref_pow)
        sweep_info = self._sa.sweep_info
        center_idx = math.ceil(sweep_info["sweep_length"] / 2 + 1)
        stop, start = int(center_idx / 2), int(center_idx + (center_idx / 2))
        floor = (np.average(amps[:stop]) + np.average(amps[start:])) / 2
        contrast = amps[center_idx] - floor
        is_tuned = contrast < self.threshold
        real_center = fs[center_idx]
        logger.info(f"Tuning check at {real_center:7E}: {contrast = :.5}dBm")
        return is_tuned, center_idx, floor

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

    def _minimize(self, fn: Callable[[tuple[float]], float]) -> tuple[float]:
        """ """
        start_time = time.perf_counter()
        opt = {
            "fatol": self.threshold,
            "initial_simplex": self.simplex,
            "maxiter": self.maxiter,
        }
        result = scipy.optimize.minimize(fn, [0, 0], method="Nelder-Mead", options=opt)
        if result.success:
            time_, contrast = time.perf_counter() - start_time, fn(result.x)
            logger.success(f"Minimized in {time_:.5}s with final {contrast = :.5}")
            if contrast > self.threshold:
                diff = contrast - self.threshold
                logger.warning(f"Final contrast exceeds threshold by {diff}dBm")
            return result.x
        else:
            logger.error(f"Minimization unsuccessful, details: {result.message}")

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
            self._sa.sweep(center=center, span=self.span, rbw=self.rbw, ref_power=self.ref_power)
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
            self._sa.sweep(center=center, span=self.span, rbw=self.rbw, ref_power=self.ref_pow)
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
