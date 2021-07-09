""" """

import math
import time
from typing import Callable

import numpy as np
import scipy.optimize
from qcrew.control.instruments.quantum_machines.qm_config_builder import QMConfig
from qcrew.control.instruments.signal_hound.sa124 import Sa124
from qcrew.control.modes.mode import Mode
from qcrew.helpers import logger
from qm.QmJob import QmJob
from qm import _Program
from qm.qua import infinite_loop_, program
from qm.QuantumMachine import QuantumMachine


class MixerTuner:
    """ """

    simplex: np.ndarray = np.array([[0.0, 0.0], [0.0, 0.1], [0.1, 0.0]])
    threshold: float = 3.0  # in dBm
    span: float = 2e6
    rbw: float = 50e3
    ref_power: float = 0.0

    def __init__(self, sa: Sa124, qm: QuantumMachine, *modes: Mode) -> None:
        """ """
        self._sa: Sa124 = sa
        self._sa.span = self.span
        self._sa.rbw = self.rbw
        self._sa.ref_power = self.ref_power
        self._qm: QuantumMachine = qm
        self._modes: tuple[Mode] = modes
        logger.info(f"Call `.tune()` to tune mixers of {self._modes}")

    def _get_qua_program(self, mode: Mode) -> _Program:
        """ """
        with program() as mixer_tuning:
            with infinite_loop_():
                mode.play("constant_pulse")
        return mixer_tuning

    def tune(self) -> None:
        """ """
        try:
            for mode in self._modes:
                mode.lo_freq = mode.lo_freq  # play carrier freq to mode
                job = self._qm.execute(self._get_qua_program(mode))  # play int freq
                self._tune_mode(mode, job)
        except AttributeError as e:
            logger.error("MixerTuner is initialized with unrecognized arguments")
            raise SystemExit("Failed to initiate mixer tuning, exiting...") from e
        else:
            self._sa.rbw = Sa124.default_rbw
            job.halt()

    def _tune_mode(self, mode: Mode, job: QmJob) -> None:
        """ """
        for key in ("LO", "SB"):
            center = mode.lo_freq if key == "LO" else mode.lo_freq - mode.int_freq
            is_tuned, center_idx, floor = self._check_tuning(center=center)
            if is_tuned:
                logger.success(f"{key} already tuned to within {self.threshold}dBm!")
            elif key == "LO":
                self._tune_lo(mode, center_idx, floor)
            elif key == "SB":
                self._tune_sb(mode, job, center_idx, floor)

    def _tune_lo(self, mode: Mode, center_idx: int, floor: float) -> None:
        """ """
        logger.info(f"Minimizing {mode} local oscillator leakage...")

        def objective_fn(offsets: tuple[float]) -> float:
            i_offset, q_offset, mode_name = offsets[0], offsets[1], mode.name
            self._qm.set_output_dc_offset_by_element(mode_name, "I", i_offset)
            self._qm.set_output_dc_offset_by_element(mode_name, "Q", q_offset)
            _, amps = self._sa.sweep()
            contrast = amps[center_idx] - floor
            return contrast

        start_time = time.perf_counter()
        result = self._minimize(objective_fn)
        if result is not None:
            time_ = time.perf_counter() - start_time
            contrast = objective_fn(result)
            logger.success(f"LO leak minimized in {time_:.5}s, final {contrast = :.5}")
            mode.offsets = {"I": result[0], "Q": result[1]}  # update mode offsets

    def _tune_sb(self, mode: Mode, job: QmJob, center_idx: int, floor: float) -> None:
        """ """
        logger.info(f"Minimizing {mode} sideband leakage...")

        def objective_fn(offsets: tuple[float]) -> float:
            correction_matrix = QMConfig.get_mixer_correction_matrix(*offsets)
            job.set_element_correction(mode.name, correction_matrix)
            _, amps = self._sa.sweep()
            contrast = amps[center_idx] - floor
            return contrast

        start_time = time.perf_counter()
        result = self._minimize(objective_fn)
        if result is not None:
            time_ = time.perf_counter() - start_time
            contrast = objective_fn(result)
            logger.success(f"SB leak minimized in {time_:.5}s, final {contrast = :.5}")
            mode.offsets = {"G": result[0], "P": result[1]}  # update mode offsets

    def _check_tuning(self, center: float) -> tuple[bool, int, float]:
        """ """
        freqs, amps = self._sa.sweep(center=center)
        sweep_info = self._sa.sweep_info
        center_idx = math.ceil(sweep_info["sweep_length"] / 2 + 1)
        stop, start = int(center_idx / 2), int(center_idx + (center_idx / 2))
        floor = (np.average(amps[:stop]) + np.average(amps[start:])) / 2
        contrast = amps[center_idx] - floor
        is_tuned = contrast < self.threshold
        real_center = freqs[center_idx]
        logger.info(f"Tuning check at {real_center:E}: {contrast = :.5}dBm")
        return is_tuned, center_idx, floor

    def _minimize(self, fn: Callable[[tuple[float]], float]) -> tuple[float]:
        """ """
        opt = {"fatol": self.threshold, "initial_simplex": self.simplex}
        result = scipy.optimize.minimize(fn, [0, 0], method="Nelder-Mead", options=opt)
        if result.success:
            return result.x
        else:
            logger.warning(f"Minimization unsuccessful, details: {result.message}")
