""" Sa124 class written to support the SA124B's frequency sweep mode. A frequency sweep displays amplitude on the vertical axis and frequency on the horizontal axis """

import time
from typing import Any, ClassVar

import numpy as np

from qcrew.control.instruments.instrument import Instrument
import qcrew.control.instruments.signal_hound.sa_api as sa
from qcrew.helpers import logger


class Sa124(Instrument):
    """ """

    _parameters: ClassVar[set[str]] = {
        "center",  # frequency sweep center, in Hz
        "span",  # frequency sweep span, in Hz
        "sweep_length",  # frequency sweep length, decided by the device
        "rbw",  # resolution bandwidth, in Hz
        "ref_power",  # reference power level in dBm
    }

    name: str = "SA"

    # pylint: disable=line-too-long, long docstrings for top-level constants are OK

    detector: int = sa.SA_AVERAGE
    """ `detector` specifies if overlapping results from signal processing should be averaged (`SA_AVERAGE`) or if minimum and maximum values should be maintained (`SA_MIN_MAX`). """

    scale: int = sa.SA_LOG_SCALE
    """ `scale` changes units of returned amplitudes. Use `SA_LOG_SCALE` for dBm, `SA_LIN_SCALE` for millivolts, and `SA_LOG_FULL_SCALE` and `SA_LIN_FULL_SCALE` for amplitudes to be returned from the full scale input. """

    rbw_shape: int = sa.SA_RBW_SHAPE_FLATTOP
    """ `rbw_shape` specifies the RBW filter shape. The shape is applied by changing the window function. If set as `SA_RBW_SHAPE_FLATTOP`, a custom bandwidth flat-top window measured at the 3dB cutoff point is used. If set as `SA_RBW_SHAPE_CISPR`, a Gaussian window with zero-padding measured at the 6dB cutoff point is used. """

    vid_proc_units: int = sa.SA_LOG_UNITS
    """ `vid_proc_units` specifies units for video processing. For “average power” measurements, `SA_POWER_UNITS` should be selected. For cleaning up an amplitude modulated signal, `SA_VOLT_UNITS` would be a good choice. To emulate a traditional spectrum analyzer, select `SA_LOG_UNITS`. To minimize processing power and bypass video bandwidth processing, select `SA_BYPASS`. """

    rej_img: int = sa.SA_TRUE
    """ `rej_img` determines whether software image reject will be performed. Generally, set reject to true for continuous signals, and false to catch short duration signals at a known frequency. """

    timebase: int = sa.SA_REF_EXTERNAL_IN
    """ `timebase` can be set to `SA_REF_EXTERNAL_IN` to use an external 10 MHz reference or `SA_REF_INTERNAL_OUT` to use an internal clock reference. """

    default_center: float = 8e9
    """ Default value for the frequency sweep center, in Hz """

    default_span: float = 500e6
    """ Default value for the frequency sweep span, in Hz """

    default_rbw: float = 250e3
    """ Default value for the resolution bandwidth (rbw), in Hz. The amplitude value for each frequency bin represents total energy from rbw / 2 below and above the bin's center. Available values are [0.1Hz-100kHz], 250kHz, 6MHz. See `_is_valid_rbw()` for exceptions to available values. """

    default_ref_power: float = 0.0
    """ Reference power level of the device in dBm. To achieve the best results, ensure gain and attenuation are set to AUTO and reference level is set at or slightly above expected input power for best sensitivity. """

    # pylint: enable=line-too-long
    # pylint: disable=redefined-builtin, intentional shadowing of `id`

    def __init__(
        self,
        id: int,
        center: float = default_center,
        span: float = default_span,
        rbw: float = default_rbw,
        ref_power: float = default_ref_power,
    ) -> None:
        super().__init__(id)
        self._handle: int = None  # will be updated by connect()
        self.connect()

        self.center: float = center
        self.span: float = span
        self.rbw: float = rbw
        self.ref_power: float = ref_power
        self._freqs: np.ndarray = None  # will be updated by _set_sweep()
        self.sweep_length: int = None  # will be updated by _set_sweep()

    # pylint: enable=redefined-builtin

    def connect(self) -> None:
        """ """
        logger.info(f"Connecting to {self}, please wait ~7 seconds...")

        if self.id in sa.ACTIVE_CONNECTIONS:
            logger.warning(f"{self} is already connected")
            self._handle = sa.ACTIVE_CONNECTIONS[self.id]
            return

        self._handle = sa.sa_open_device_by_serial(self.id)["handle"]
        sa.ACTIVE_CONNECTIONS[self.id] = self._handle
        logger.info(f"Connected to {self}")
        self._initialize()

    def _initialize(self) -> None:
        """ """

        # use external 10MHz reference
        sa.sa_set_timebase(self._handle, Sa124.timebase)
        # configure acquisition settings
        sa.sa_config_acquisition(self._handle, Sa124.detector, Sa124.scale)
        # configure rbw filter shape
        sa.sa_config_RBW_shape(self._handle, Sa124.rbw_shape)
        # configure video processing unit type
        sa.sa_config_proc_units(self._handle, Sa124.vid_proc_units)

        # set sweep parameters
        self._set_sweep(
            center=self.center, span=self.span, rbw=self.rbw, ref_power=self.ref_power
        )

    @property  # sweep info getter
    def sweep_info(self) -> dict[str, float]:
        """ """
        return sa.sa_query_sweep_info(self._handle)

    def sweep(self, **sweep_params) -> tuple[np.ndarray, np.ndarray]:
        """ """
        if sweep_params:
            return self._sweep_with_params(**sweep_params)
        amps = sa.sa_get_sweep_64f(self._handle)["max"]
        return self._freqs, amps  # self._freqs has been updated by _set_sweep()

    def _sweep_with_params(self, **sweep_params) -> tuple[np.ndarray, np.ndarray]:
        """ """
        self._set_sweep(**sweep_params)
        length, center, span = self.sweep_length, self.center, self.span
        logger.info(f"Sweeping {length} points with {center = }, {span = }...")
        start_time = time.perf_counter()
        amps = sa.sa_get_sweep_64f(self._handle)["max"]
        elapsed_time = time.perf_counter() - start_time
        logger.info(f"Sweep done in {elapsed_time:.5}s")
        return self._freqs, amps  # self._freqs has been updated by _set_sweep()

    def _set_sweep(self, **sweep_params) -> None:
        """ """
        sa.sa_initiate(self._handle, sa.SA_IDLE, sa.SA_FALSE)  # idle before configuring

        if "center" in sweep_params:
            self._set_center(sweep_params["center"])  # set instance attribute
        if "span" in sweep_params:
            self._set_span(sweep_params["span"])  # set instance attribute
        sa.sa_config_center_span(self._handle, self.center, self.span)  # set on device

        if "rbw" in sweep_params:
            self._set_rbw(sweep_params["rbw"])  # set instance attribute
            sa.sa_config_sweep_coupling(self._handle, self.rbw, self.rbw, self.rej_img)

        if "ref_power" in sweep_params:
            self._set_ref_power(sweep_params["ref_power"])  # set instance attribute
            sa.sa_config_level(self._handle, self.ref_power)

        sa.sa_initiate(self._handle, sa.SA_SWEEPING, sa.SA_FALSE)  # ready to sweep

        sweep_info = self.sweep_info
        f_start = sweep_info["start_freq"]
        bin_size = sweep_info["bin_size"]
        sweep_len = sweep_info["sweep_length"]
        self._freqs = [f_start + i * bin_size for i in range(sweep_len)]
        self.sweep_length = len(self._freqs)

    def _set_center(self, center: float) -> None:
        """ """
        if not sa.MIN_CENTER <= center <= sa.MAX_CENTER:
            logger.error(f"Center out of bounds [{sa.MIN_CENTER, sa.MAX_CENTER}]")
            raise ValueError("Value out of bounds")
        self.center = center
        logger.success(f"Set frequency sweep center to {self.center:E} Hz")

    def _set_span(self, span: float) -> None:
        """ """
        if span < sa.MIN_SPAN:
            logger.warning(f"Span set to minimum value of {sa.MIN_SPAN} Hz")
            self.span = sa.MIN_SPAN
        elif self.center + span > sa.MAX_CENTER or self.center - span < sa.MIN_CENTER:
            logger.error(f"Sweep range out of bounds [{sa.MIN_CENTER, sa.MAX_CENTER}]")
            raise ValueError("Value out of bounds")
        else:
            self.span = span
            logger.success(f"Set frequency sweep span to {self.span:E} Hz")

    def _set_rbw(self, rbw: float) -> None:
        """ """
        start = self.center - (self.span / 2)
        # is_valid_rbw conditions are obtained from the SA124 API manual
        is_valid_rbw = False
        if (rbw == 6e6 and start >= 2e8 and self.span >= 2e8) or rbw == 250e3:
            is_valid_rbw = True
        elif 0.1 <= rbw <= 1e5:
            is_valid_rbw = True
            if (self.span >= 1e8 or (self.span > 2e5 and start < 16e6)) and rbw < 6.5e3:
                is_valid_rbw = False

        if not is_valid_rbw:
            logger.warning(f"Invalid {rbw = }, set to default {Sa124.default_rbw:E} Hz")
            self.rbw = Sa124.default_rbw
        else:
            self.rbw = rbw
            logger.success(f"Set frequency sweep rbw to {self.rbw:E} Hz")

    def _set_ref_power(self, ref_power: float) -> None:
        """ """
        if ref_power > sa.MAX_REF_POWER:
            logger.warning(f"Ref power set to maximum value of {sa.MAX_REF_POWER} Hz")
            self.ref_power = sa.MAX_REF_POWER
        else:
            self.ref_power = ref_power
            logger.success(f"Set ref power to {self.ref_power} dBm")

    def disconnect(self) -> None:
        """ """
        sa.sa_close_device(self._handle)
        del sa.ACTIVE_CONNECTIONS[self.id]
        logger.info(f"Disconnected {self}")
