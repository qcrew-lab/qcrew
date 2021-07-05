""" """

import math
from typing import Callable

import numpy as np
import scipy.optimize
from qcrew.control.instruments.quantum_machines.qm_config_builder import QMConfig
from qcrew.control.instruments.signal_hound.sa124 import Sa124
from qcrew.control.modes.mode import Mode
from qcrew.helpers import logger
from qm.qua import infinite_loop_, program  # TODO
from qm.QuantumMachine import QuantumMachine  # TODO


class MixerTuner:
    """ """

    simplex: np.ndarray = np.array([[0.0, 0.0], [0.0, 0.1], [0.1, 0.0]])
    threshold: float = 1.0  # in dBm
    span: float = 2e6  # TODO
    rbw: float = 50e3  # TODO
    ref_power: float = 0.0  # TODO

    def __init__(self, sa: Sa124, qm: QuantumMachine, *modes: Mode) -> None:
        """ """
        self._sa: Sa124 = sa
        self._qm: QuantumMachine = qm
        self._modes: tuple[Mode] = modes
        logger.info(f"Call `.tune()` to tune mixers of {self._modes}")

    def _get_qua_program(self, mode: Mode):  # -> ? TODO
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
                self._tune_lo(mode)
                self._tune_sb(mode, job)
        except AttributeError as e:
            logger.error("MixerTuner is initialized with unrecognized arguments")
            raise SystemExit("Failed to initiate mixer tuning, exiting...") from e
        else:
            job.halt()

    def _tune_lo(self, mode: Mode) -> None:
        """ """
        logger.info(f"Minimizing {mode} local oscillator leakage...")
        is_tuned, center_idx, floor = self._check_tuning(center=mode.lo_freq)
        if is_tuned:
            logger.success(f"LO already tuned to within {self.threshold}dBm!")
            return

        def objective_fn(offsets: tuple[float]) -> float:
            i_offset, q_offset, mode_name = offsets[0], offsets[1], mode.name
            self._qm.set_output_dc_offset_by_element(mode_name, "I", i_offset)
            self._qm.set_output_dc_offset_by_element(mode_name, "Q", q_offset)
            _, amps = self._sa.sweep()
            contrast = amps[center_idx] - floor
            logger.debug(f"{i_offset = }, {q_offset = }, {contrast = }")
            return contrast

        i_offset, q_offset = self._minimize(objective_fn)
        mode.offsets = {"I": i_offset, "Q": q_offset}  # update mode offsets

    def _tune_sb(self, mode: Mode, job) -> None:  # TODO qm job typing hint
        """ """
        logger.info(f"Minimizing {mode} sideband leakage...")
        sb_freq = mode.lo_freq - mode.int_freq
        is_tuned, center_idx, floor = self._check_tuning(center=sb_freq)
        if is_tuned:
            logger.info(f"SB already tuned to within {self.threshold}dBm!")
            return

        def objective_fn(offsets: tuple[float]) -> float:
            correction_matrix = QMConfig.get_mixer_correction_matrix(*offsets)
            job.set_element_correction(mode.name, correction_matrix)
            _, amps = self._sa.sweep()
            contrast = amps[center_idx] - floor
            logger.debug(f"{offsets = }, {contrast = }")
            return contrast

        g_offset, p_offset = self._minimize(objective_fn)
        mode.offsets = {"G": g_offset, "P": p_offset}  # update mode offsets

    def _check_tuning(self, center: float) -> tuple[bool, int, float]:
        """ """
        span, rbw, power = self.span, self.rbw, self.ref_power
        freqs, amps = self._sa.sweep(center=center, span=span, rbw=rbw, ref_power=power)
        sweep_info = self._sa.sweep_info
        center_idx = math.ceil(sweep_info["sweep_length"] / 2 + 1)
        stop, start = int(center_idx / 2), int(center_idx + (center_idx / 2))
        floor = (np.average(amps[:stop]) + np.average(amps[start:])) / 2
        contrast = amps[center_idx] - floor
        is_tuned = contrast < self.threshold
        logger.debug(f"{floor = }dBm, {contrast = }dBm at {freqs[center_idx]:E}Hz")
        return is_tuned, center_idx, floor

    def _minimize(self, fn: Callable[[tuple[float]], float]) -> tuple[float]:
        """ """
        opt = {"fatol": self.threshold, "initial_simplex": self.simplex}
        result = scipy.optimize.minimize(fn, [0, 0], method="Nelder-Mead", options=opt)
        if result.success:
            results = result.x
            logger.success(f"Minimization completed successfully with {results = }")
            return results[0], results[1]
        else:
            logger.warning(f"Minimization unsuccessful, details: {result.message}")
