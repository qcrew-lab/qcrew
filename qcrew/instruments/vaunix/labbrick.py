"""
Python driver for Vaunix Signal Generator LMS (LabBrick).
"""

from dataclasses import InitVar, dataclass, field
from typing import ClassVar, NoReturn, Union

from qcrew.helpers import logger
from qcrew.instruments import PhysicalInstrument
from qcrew.instruments.vaunix.labbrick_api import (
    vnx_connect_to_device,
    vnx_close_device,
    vnx_get_frequency,
    vnx_get_power,
    vnx_get_rf_on,
    vnx_set_frequency,
    vnx_set_power,
    vnx_set_rf_on,
    vnx_set_use_internal_ref,
)


@dataclass
class LabBrick(PhysicalInstrument):
    """ """

    # class variable defining the parameter set for LabBrick objects
    _parameters: ClassVar[frozenset[str]] = frozenset(["frequency", "power"])

    frequency: InitVar[float]
    power: InitVar[float]

    _handle: int = field(default=None, init=False, repr=False)

    def __post_init__(self, frequency: float, power: float) -> NoReturn:
        """ """
        self._handle = self._connect()
        self._initialize(frequency, power)

    def _connect(self) -> int:
        """ """
        try:
            device_handle = vnx_connect_to_device(self.id)
        except ConnectionError:
            logger.exception(f"Failed to connect to LB{self.id}")
            raise
        else:
            logger.info(f"Connected to LB{self.id}")
            return device_handle

    def _initialize(self, frequency: float, power: float) -> NoReturn:
        """ """
        vnx_set_use_internal_ref(self._handle, False)  # use external 10MHz reference
        self.toggle_rf()  # turn on RF, guaranteed to be off

        # set labbrick at initial frequency and power, if specified as float or int
        # type check needed as frequency and power are implicitly set as property type
        # when not explicitly passed in __init__() by the user
        if isinstance(frequency, (float, int)):
            self.frequency = frequency
        if isinstance(power, (float, int)):
            self.power = power

    def toggle_rf(self) -> NoReturn:
        """ """
        toggle = not vnx_get_rf_on(self._handle)
        vnx_set_rf_on(self._handle, toggle)
        logger.success(f"LB{self.id} RF is {'ON' if toggle else 'OFF'}")

    # pylint: disable=function-redefined, intentional shadowing of InitVar frequency

    @property  # frequency getter
    def frequency(self) -> float:
        """ """
        try:
            current_frequency = vnx_get_frequency(self._handle)
        except ValueError:
            logger.exception(f"LB{self.id} failed to get frequency")
            raise
        else:
            logger.success(f"LB{self.id} got frequency {current_frequency:.7E} Hz")
            return current_frequency

    # pylint: enable=function-redefined

    @frequency.setter
    def frequency(self, new_frequency: Union[int, float]) -> NoReturn:
        """ """
        try:
            current_frequency = vnx_set_frequency(self._handle, new_frequency)
        except (TypeError, ValueError, ConnectionError):
            logger.exception("LB{} failed to set frequency", self.id)
            raise
        else:
            logger.success(f"LB{self.id} set frequency {current_frequency:.7E} Hz")

    # pylint: disable=function-redefined, intentional shadowing of InitVar power

    @property  # power getter
    def power(self) -> float:
        """ """
        try:
            current_power = vnx_get_power(self._handle)
        except ValueError:
            logger.exception(f"LB{self.id} failed to get power")
            raise
        else:
            logger.success(f"LB{self.id} got power {current_power} dBm")
            return current_power

    # pylint: enable=function-redefined

    @power.setter
    def power(self, new_power: Union[int, float]) -> NoReturn:
        """ """
        try:
            current_power = vnx_set_power(self._handle, new_power)
        except (TypeError, ValueError, ConnectionError):
            logger.exception(f"LB{self.id} failed to set power")
            raise
        else:
            logger.success(f"LB{self.id} set power {current_power} dBm")

    def disconnect(self):
        """ """
        if vnx_get_rf_on(self._handle):
            self.toggle_rf()  # turn off RF if on

        try:
            vnx_close_device(self._handle)
        except ConnectionError:
            logger.exception(f"Failed to close LB{self.id}")
            raise
        else:
            logger.info(f"Disconnected LB{self.id}")
