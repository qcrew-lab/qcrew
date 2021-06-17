""" """

from typing import ClassVar

import qcrew.control.instruments.vaunix.labbrick_api as vnx
from qcrew.helpers import logger
from qcrew.control.instruments.instrument import Instrument


class LabBrick(Instrument):
    """ """

    _parameters: ClassVar[set[str]] = {"frequency", "power"}

    # pylint: disable=redefined-builtin, intentional shadowing of `id`

    def __init__(self, id: int, frequency: float = None, power: float = None) -> None:
        """ """
        super().__init__(id)
        self._handle: int = None  # will be updated by self._connect()
        self._connect()
        self._initialize(frequency, power)

    # pylint: enable=redefined-builtin

    def _connect(self) -> None:
        """ """
        try:
            device_handle = vnx.connect_to_device(self.id)
        except ConnectionError as e:
            logger.exception(f"Failed to connect to LB{self.id}")
            raise SystemExit("LabBrick connection error, exiting...") from e

        else:
            logger.info(f"Connected to {self}, call .parameters to get current state")
            self._handle = device_handle

    def _initialize(self, frequency: float, power: float) -> None:
        """ """
        vnx.set_use_internal_ref(self._handle, False)  # use external 10MHz reference
        self.toggle_rf()  # turn on RF, guaranteed to be off

        # if user specifies initial frequency and power, set them
        # else, get current frequency and power from device and set those
        self.frequency = frequency if frequency is not None else self.frequency
        self.power = power if power is not None else self.power

    def toggle_rf(self) -> None:
        """ """
        toggle = not vnx.get_rf_on(self._handle)
        vnx.set_rf_on(self._handle, toggle)
        logger.success(f"LB{self.id} RF is {'ON' if toggle else 'OFF'}")

    @property  # frequency getter
    def frequency(self) -> float:
        """ """
        try:
            frequency = vnx.get_frequency(self._handle)
        except ConnectionError as e:
            logger.exception(f"LB{self.id} failed to get frequency")
            raise SystemExit("LabBrick is disconnected, exiting...") from e
        else:
            logger.success(f"LB{self.id} current {frequency:.7E = } Hz")
            return frequency

    @frequency.setter
    def frequency(self, new_frequency: float) -> None:
        """ """
        try:
            frequency = vnx.set_frequency(self._handle, new_frequency)
        except (TypeError, ValueError):
            logger.exception(f"LB{self.id} failed to set frequency")
        except ConnectionError as e:
            logger.exception(f"LB{self.id} failed to set frequency")
            raise SystemExit("LabBrick is disconnected, exiting...") from e
        else:
            logger.success(f"LB{self.id} set {frequency:.7E = } Hz")

    @property  # power getter
    def power(self) -> float:
        """ """
        try:
            power = vnx.get_power(self._handle)
        except ConnectionError:
            logger.exception(f"LB{self.id} failed to get power")
            raise SystemExit("LabBrick is disconnected, exiting...") from e
        else:
            logger.success(f"LB{self.id} current {power = } dBm")
            return power

    @power.setter
    def power(self, new_power: float) -> None:
        """ """
        try:
            power = vnx.set_power(self._handle, new_power)
        except (TypeError, ValueError):
            logger.exception(f"LB{self.id} failed to set power")
        except ConnectionError as e:
            logger.exception(f"LB{self.id} failed to set power")
            raise SystemExit("LabBrick is disconnected, exiting...") from e
        else:
            logger.success(f"LB{self.id} set {power = } dBm")

    def disconnect(self) -> None:
        """ """
        if vnx.get_rf_on(self._handle):
            self.toggle_rf()  # turn off RF if on

        try:
            vnx.close_device(self._handle)
        except ConnectionError as e:
            logger.exception(f"Failed to close LB{self.id}")
            raise SystemExit("LabBrick connection error, exiting...") from e
        else:
            logger.info(f"Disconnected {self}")
