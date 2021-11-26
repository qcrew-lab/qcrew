""" """

from ctypes import (
    c_char_p,
    c_void_p,
    c_ulonglong,
    c_float,
    CDLL,
    c_ubyte,
    POINTER,
    Structure,
    c_uint,
    c_ushort,
)
import pathlib

from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger


class RFParams(Structure):
    _fields_ = [
        ("rf1_freq", c_ulonglong),
        ("start_freq", c_ulonglong),
        ("stop_freq", c_ulonglong),
        ("step_freq", c_ulonglong),
        ("sweep_dwell_time", c_uint),
        ("sweep_cycles", c_uint),
        ("buffer_points", c_uint),
        ("rf_level", c_float),
        ("rf2_freq", c_ushort),
    ]


class DeviceStatus(Structure):
    class ListMode(Structure):
        _fields_ = [
            (name, c_ubyte)
            for name in (
                "sss_mode",
                "sweep_dir",
                "tri_waveform",
                "hw_trigger",
                "step_on_hw_trig",
                "return_to_start",
                "trig_out_enable",
                "trig_out_on_cycle",
            )
        ]

    class PLLStatus(Structure):
        _fields_ = [
            (name, c_ubyte)
            for name in (
                "sum_pll_ld",
                "crs_pll_ld",
                "fine_pll_ld",
                "crs_ref_pll_ld",
                "crs_aux_pll_ld",
                "ref_100_pll_ld",
                "ref_10_pll_ld",
                "rf2_pll_ld",
            )
        ]

    class OperateStatus(Structure):
        _fields_ = [
            (name, c_ubyte)
            for name in (
                "rf1_lock_mode",
                "rf1_loop_gain",
                "device_access",
                "rf2_standby",
                "rf1_standby",
                "auto_pwr_disable",
                "alc_mode",
                "rf1_out_enable",
                "ext_ref_lock_enable",
                "ext_ref_detect",
                "ref_out_select",
                "list_mode_running",
                "rf1_mode",
                "over_temp",
                "harmonic_ss",
            )
        ]

    _fields_ = [
        ("list_mode", ListMode),
        ("operate_status", OperateStatus),
        ("pll_status", PLLStatus),
    ]


DLLNAME = "sc5511a.dll"
DRIVERPATH = pathlib.Path(__file__).resolve().parent / DLLNAME
SC = CDLL(str(DRIVERPATH))

SC.sc5511a_open_device.argtypes = [c_char_p]
SC.sc5511a_open_device.restype = c_void_p
SC.sc5511a_close_device.argtypes = [c_void_p]
SC.sc5511a_set_freq.argtypes = [c_void_p, c_ulonglong]
SC.sc5511a_set_level.argtypes = [c_void_p, c_float]
SC.sc5511a_set_output.argtypes = [c_void_p, c_ubyte]
SC.sc5511a_set_clock_reference.argtypes = [c_void_p, c_ubyte, c_ubyte]
SC.sc5511a_get_rf_parameters.argtypes = [c_void_p, POINTER(RFParams)]
SC.sc5511a_get_device_status.argtypes = [c_void_p, POINTER(DeviceStatus)]


class CoreA(Instrument):
    """ """

    def __init__(self, id, name="Core_A"):
        """ """
        super().__init__(id, name=name)
        self._handle: int = None  # will be updated by self.connect()
        self.connect()
        self._initialize()

    def connect(self):
        """ """
        self._handle = SC.sc5511a_open_device(str(self.id).encode())
        logger.info(f"Connected to {self}")

    def _initialize(self):
        """ """
        # 0 = 10 MHz ref out signal, 1 = locks to external reference
        SC.sc5511a_set_clock_reference(self._handle, 0, 1)
        self.rf = False

    def disconnect(self):
        """ """
        SC.sc5511a_close_device(self._handle)
        self.rf = False
        logger.info(f"Disconnected {self}")

    @property
    def rf_params(self):
        """ """
        rf_params = RFParams()
        SC.sc5511a_get_rf_parameters(self._handle, rf_params)
        return rf_params

    @property
    def status(self):
        status = DeviceStatus()
        SC.sc5511a_get_device_status(self._handle, status)
        return status

    @property  # rf on getter
    def rf(self) -> bool:
        """ """
        value = self.status.operate_status.rf1_out_enable
        logger.info(f"{self} rf is {'ON' if value else 'OFF'}")
        return bool(value)

    @rf.setter
    def rf(self, toggle: bool) -> None:
        """ """
        SC.sc5511a_set_output(self._handle, int(toggle))
        logger.info(f"{self} rf is {'ON' if toggle else 'OFF'}")

    @property
    def frequency(self) -> int:
        """ """
        value = self.rf_params.rf1_freq
        logger.info(f"{self} frequency = {value:E}")
        return value

    @frequency.setter
    def frequency(self, value: float) -> None:
        """ """
        SC.sc5511a_set_freq(self._handle, int(value))
        logger.info(f"Set {self} frequency: {value:E}")

    @property
    def power(self) -> float:
        """ """
        value = self.rf_params.rf_level
        logger.info(f"{self} power = {value}")
        return value

    @power.setter
    def power(self, value: float) -> None:
        """ """
        SC.sc5511a_set_level(self._handle, value)
        logger.info(f"Set {self} power: {value}")
