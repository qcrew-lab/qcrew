""" """

import ctypes
import pathlib

from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger

DLLNAME = "sc5511a.dll"
DRIVERPATH = pathlib.Path(__file__).resolve().parent / DLLNAME
SC = ctypes.CDLL(str(DRIVERPATH))

class SC5511A(Instrument):
    """ """

    def __init__(self, id, name):
        """ """
        super().__init__(id, name=name)
        self._handle: int = None  # will be updated by self.connect()
        self.connect()
        self._initialize()

    def connect(self):
        """ """
        self._handle = SC.sc5511a_open_device(self.id)
        logger.info(f"Handle is: {self._handle}, type: {type(self._handle)}")
        info = SC.sc5511a_get_device_info(self._handle)
        logger.info(f"Connected to {self}: {info}")

    def _initialize(self):
        """ """
        # 0 = 10 MHz, 1 = locks to external reference
        SC.sc5511a_set_clock_reference(self._handle, 0, 1)

    def disconnect(self):
        """ """
        SC.sc5511a_close_device(self._handle)

    @property  # rf on getter
    def rf(self) -> bool:
        """ """
        

    @rf.setter
    def rf(self, toggle: bool) -> None:
        """ """
        SC.sc5511a_set_output(self._handle, int(toggle))
        logger.info(f"{self} rf is {'ON' if toggle else 'OFF'}")

    @property
    def frequency(self) -> float:
        """ """
        frequency = ctypes.c_ulonglong()
        SC.sc5511a_reg_read(self._handle, "GET_RF_PARAMETERS", 0, frequency)
        logger.info(f"Got {self} {frequency = }")

    @frequency.setter
    def frequency(self, value: float) -> None:
        """ """
        SC.sc5511a_set_freq(self._handle, value)
        logger.info(f"Set {self} frequency: {value}")

    @property
    def power(self) -> float:
        """ """
        power = ctypes.c_float()
        SC.sc5511a_reg_read(self._handle, "GET_RF_PARAMETERS", 0x07, power)
        logger.info(f"Got {self} {power = }")

    @power.setter
    def power(self, value: float) -> None:
        """ """
        SC.sc5511a_set_level(self._handle, value)
        logger.info(f"Set {self} power: {value}")
