"""
Python driver for Vaunix Signal Generator LMS (LabBrick).
"""

from dataclasses import InitVar, dataclass, field
from typing import Any, NoReturn, Union

from qcrew.helpers import logger
from qcrew.instruments import PhysicalInstrument
from qcrew.instruments.vaunix.labbrick_api import (
    vnx_connect_to_device,
    vnx_close_device,
    vnx_get_frequency,
    vnx_get_power,
    vnx_set_frequency,
    vnx_set_power,
    vnx_set_rf_on,
    vnx_set_use_internal_ref,
)

PARAM_DICT = {"frequency": None, "power": None}


@dataclass
class LabBrick(PhysicalInstrument):
    """ """

    frequency: InitVar[float]
    power: InitVar[float]

    _parameters: dict[str, Any] = field(default_factory=PARAM_DICT.copy, init=False)
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
            logger.exception("Failed to connect to LB{}", self.id)
            raise
        else:
            self._status["connected"] = True
            logger.info("Connected to LB{}", self.id)
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
        toggle = not self._status["running"]
        vnx_set_rf_on(self._handle, toggle)
        self._status["running"] = toggle
        logger.success(
            "LB{} RF is {state}".format(self.id, state="ON" if toggle else "OFF")
        )

    @property  # frequency getter
    def frequency(self) -> float:
        """ """
        try:
            current_frequency = vnx_get_frequency(self._handle)
        except ValueError:
            logger.exception("LB{} failed to get frequency", self.id)
            raise
        else:
            self._parameters["frequency"] = current_frequency
            logger.success("LB{} got frequency {:.7E} Hz", self.id, current_frequency)
            return current_frequency

    @frequency.setter
    def frequency(self, new_frequency: Union[int, float]) -> NoReturn:
        """ """
        try:
            current_frequency = vnx_set_frequency(self._handle, new_frequency)
        except (TypeError, ValueError, ConnectionError):
            logger.exception("LB{} failed to set frequency", self.id)
            raise
        else:
            self._parameters["frequency"] = current_frequency
            logger.success("LB{} set frequency {:.7E} Hz", self.id, current_frequency)

    @property  # power getter
    def power(self) -> float:
        """ """
        try:
            current_power = vnx_get_power(self._handle)
        except ValueError:
            logger.exception("LB{} failed to get power", self.id)
            raise
        else:
            self._parameters["power"] = current_power
            logger.success("LB{} got power {} dBm", self.id, current_power)
            return current_power

    @power.setter
    def power(self, new_power: Union[int, float]) -> NoReturn:
        """ """
        try:
            current_power = vnx_set_power(self._handle, new_power)
        except (TypeError, ValueError, ConnectionError):
            logger.exception("LB{} failed to set power", self.id)
            raise
        else:
            self._parameters["power"] = current_power
            logger.success("LB{} set power {} dBm", self.id, current_power)

    def disconnect(self):
        """ """
        try:
            vnx_close_device(self._handle)
        except ConnectionError:
            logger.exception("Failed to close LB{}", self.id)
            raise
        else:
            self._status["connected"] = False
            logger.info("Disconnected LB{}", self.id)

            if self._status["running"]:
                self.toggle_rf()  # turn off RF if on
