""" """

from ctypes import (
    CDLL,
    Structure,
    POINTER,
    byref,
    c_float,
    c_int,
    c_ubyte,
    c_ushort,
    c_uint,
    c_ulonglong,
    c_void_p,
    c_char_p,
)
import pathlib

from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger


class RFParameters(Structure):
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
SC.sc5503b_GetRfParameters.argtypes = [c_void_p, POINTER(RFParameters)]
SC.sc5503b_GetDeviceStatus.argtypes = [c_void_p, POINTER(DeviceStatus)]

