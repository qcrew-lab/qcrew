""" """

from ctypes import (
    CDLL,
    Structure,
    POINTER,
    byref,
    c_float,
    c_ubyte,
    c_ulonglong,
    c_void_p,
    c_char_p,
    c_uint8,
)
import pathlib
from typing import ClassVar

from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger


class RFParams(Structure):
    _fields_ = [("frequency", c_ulonglong), ("powerLevel", c_float),] + [
        (name, c_ubyte)
        for name in (
            "rfEnable",
            "alcOpen",
            "autoLevelEnable",
            "fastTune",
            "tuneStep",
            "referenceSetting",
        )
    ]


class DeviceStatus(Structure):
    _fields_ = [
        (name, c_ubyte)
        for name in (
            "tcxoPllLock",
            "vcxoPllLock",
            "finePllLock",
            "coarsePllLock",
            "sumPllLock",
            "extRefDetected",
            "refClkOutEnable",
            "extRefLockEnable",
            "alcOpen",
            "fastTuneEnable",
            "standbyEnable",
            "rfEnable",
            "pxiClkEnable",
        )
    ]


DLLNAME = "sc5503b.dll"
DRIVERPATH = pathlib.Path(__file__).resolve().parent / DLLNAME
SC = CDLL(str(DRIVERPATH))

SC.sc5503b_OpenDevice.argtypes = [c_char_p, POINTER(c_void_p)]
SC.sc5503b_CloseDevice.argtypes = [c_void_p]
SC.sc5503b_SetFrequency.argtypes = [c_void_p, c_ulonglong]
SC.sc5503b_SetPowerLevel.argtypes = [c_void_p, c_float]
SC.sc5503b_SetRfOutput.argtypes = [c_void_p, c_ubyte]
SC.sc5503b_GetRfParameters.argtypes = [c_void_p, POINTER(RFParams)]
SC.sc5503b_GetDeviceStatus.argtypes = [c_void_p, POINTER(DeviceStatus)]
SC.sc5503b_SetClockReference.argtypes = [c_void_p, c_uint8, c_uint8, c_uint8, c_uint8]


class CoreB(Instrument):
    """ """

    _parameters: ClassVar[set[str]] = {"frequency", "power", "rf"}

    def __init__(self, id, name="Core_B"):
        """ """
        super().__init__(id, name=name)
        self._handle: int = None  # will be updated by self.connect()
        self.connect()
        self._initialize()

    def connect(self):
        """ """
        self._handle = c_void_p()
        status = SC.sc5503b_OpenDevice(str(self.id).encode(), byref(self._handle))
        if status:  # non zero status values indicate error
            raise RuntimeError(f"Unable to connect to {self}, got {status = }")
        logger.info(f"Connected to {self}")

    def _initialize(self):
        """ """
        SC.sc5503b_SetClockReference(self._handle, 1, 0, 0, 0)
        self.rf = False

    def disconnect(self):
        """ """
        self.rf = False
        SC.sc5503b_CloseDevice(self._handle)
        logger.info(f"Disconnected {self}")

    @property
    def rf_params(self):
        """ """
        rf_params = RFParams()
        SC.sc5503b_GetRfParameters(self._handle, rf_params)
        return rf_params

    @property
    def status(self):
        status = DeviceStatus()
        SC.sc5503b_GetDeviceStatus(self._handle, status)
        return status

    @property  # rf on getter
    def rf(self) -> bool:
        """ """
        value = self.status.rfEnable
        logger.info(f"{self} rf is {'ON' if value else 'OFF'}")
        return bool(value)

    @rf.setter
    def rf(self, toggle: bool) -> None:
        """ """
        SC.sc5503b_SetRfOutput(self._handle, int(toggle))
        logger.info(f"{self} rf is {'ON' if toggle else 'OFF'}")

    @property
    def frequency(self) -> int:
        """ """
        value = self.rf_params.frequency
        logger.info(f"{self} frequency = {value:E}")
        return value

    @frequency.setter
    def frequency(self, value: float) -> None:
        """ """
        SC.sc5503b_SetFrequency(self._handle, int(value))
        logger.info(f"Set {self} frequency: {value:E}")

    @property
    def power(self) -> float:
        """ """
        value = self.rf_params.powerLevel
        logger.info(f"{self} power = {value}")
        return value

    @power.setter
    def power(self, value: float) -> None:
        """ """
        SC.sc5503b_SetPowerLevel(self._handle, value)
        logger.info(f"Set {self} power: {value}")
