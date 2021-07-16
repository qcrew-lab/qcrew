""" """

from typing import ClassVar

import qcrew.control.instruments.vaunix.labbrick_api as vnx
from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger


class LabBrick(Instrument):
    """ """

    _parameters: ClassVar[set[str]] = {"frequency", "power", "rf"}

    # pylint: disable=redefined-builtin, intentional shadowing of `id`

    def __init__(
        self,
        id: int,
        *,
        name: str = "LB",
        frequency: float = None,
        power: float = None,
    ) -> None:
        """ """
        super().__init__(id, name=name)
        self._handle: int = None  # will be updated by self.connect()
        self.connect()
        self._initialize(frequency=frequency, power=power)

    # pylint: enable=redefined-builtin

    def connect(self) -> None:
        """ """
        if self.id in vnx.ACTIVE_CONNECTIONS:
            logger.warning(f"{self} is already connected")
            self._handle = vnx.ACTIVE_CONNECTIONS[self.id]
            return

        try:
            device_handle = vnx.connect_to_device(self.id)
        except ConnectionError:
            logger.error(f"Failed to connect to {self}")
            raise
        else:
            self._handle = device_handle
            vnx.ACTIVE_CONNECTIONS[self.id] = self._handle
            logger.info(f"Connected to {self}")

    def _initialize(self, frequency: float, power: float) -> None:
        """ """
        vnx.set_use_internal_ref(self._handle, False)  # use external 10MHz reference

        # if user specifies initial frequency and power, set them
        # else, get current frequency and power from device, set them
        self.frequency = frequency if frequency is not None else self.frequency
        self.power = power if power is not None else self.power

    @property  # rf on getter
    def rf(self) -> bool:
        """ """
        is_on = vnx.get_rf_on(self._handle)
        return bool(is_on)

    @rf.setter
    def rf(self, toggle: bool) -> None:
        """ """
        vnx.set_rf_on(self._handle, toggle)
        logger.info(f"{self} RF is {'ON' if toggle else 'OFF'}")

    @property  # frequency getter
    def frequency(self) -> float:
        """ """
        try:
            frequency = vnx.get_frequency(self._handle)
        except ConnectionError:
            logger.error(f"{self} failed to get frequency")
            raise
        else:
            return frequency

    @frequency.setter
    def frequency(self, new_frequency: float) -> None:
        """ """
        try:
            frequency = vnx.set_frequency(self._handle, new_frequency)
        except (TypeError, ValueError, ConnectionError):
            logger.error(f"{self} failed to set frequency")
            raise
        else:
            logger.success(f"{self} set {frequency = :E} Hz")
            if not self.rf:
                self.rf = True

    @property  # power getter
    def power(self) -> float:
        """ """
        try:
            power = vnx.get_power(self._handle)
        except ConnectionError:
            logger.error(f"{self} failed to get power")
            raise
        else:
            return power

    @power.setter
    def power(self, new_power: float) -> None:
        """ """
        try:
            power = vnx.set_power(self._handle, new_power)
        except (TypeError, ValueError, ConnectionError):
            logger.exception(f"{self} failed to set power")
            raise
        else:
            logger.success(f"{self} set {power = } dBm")

    def disconnect(self) -> None:
        """ """
        self.rf = False  # turn off RF
        try:
            vnx.close_device(self._handle)
        except ConnectionError:
            logger.error(f"Failed to close {self}")
            raise
        else:
            del vnx.ACTIVE_CONNECTIONS[self.id]
            logger.info(f"Disconnected {self}")
