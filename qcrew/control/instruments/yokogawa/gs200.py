""" """

import pyvisa

from qcrew.control.instruments.instrument import Instrument
from qcrew.helpers import logger


class Yoko(Instrument):
    """ """

    def __init__(self, id: str, name="") -> None:
        """ """
        super().__init__(id=id, name=name)
        self.handle = None  # updated by connect()
        self.connect()

    def connect(self) -> None:
        """ """
        resource_name = f"USB0::0xB21::0x39::{self.id}::INSTR"
        self.handle = pyvisa.ResourceManager().open_resource(resource_name)
        logger.info(self.handle.query("*IDN?"))
        self._initialize()

    def _initialize(self) -> None:
        """ """
        # do a self-test to see if instrument is ok
        status = self.handle.query("*TST?")
        if not status == 0:  # all good
            raise RuntimeError("{self} self-test failed, please check the instrument")

    @property
    def state(self) -> str:
        """ """
        value = self.handle.query(":output?")
        return "on" if value else "off"

    @state.setter
    def state(self, value):
        """ """
        value = str(value).lower()
        valid_values = ("0", "1", "on", "off")
        if value not in valid_values:
            raise ValueError(f"Invalid {value = }, {valid_values = }")
        self.handle.write(f"output {value}")

    @property
    def source(self) -> str:
        """ """
        return self.handle.query(":source:function?")

    @source.setter
    def source(self, value: str) -> None:
        """ """
        try:
            value = value.lower()
        except AttributeError:
            logger.error(f"Expect string value, got {value = } of type {type(value)}")
            raise
        else:
            valid_values = ("volt", "voltage", "curr", "current")
            if value not in valid_values:
                raise ValueError(f"Invalid {value = }, {valid_values = }")
            self.state = "off"
            self.handle.write(f":source:function {value}")

    @property
    def level(self) -> float:
        """ """
        return float(self.handle.query(":source:level?"))

    @level.setter
    def level(self, value):
        """ """
        # TODO bound, error handle
        self.handle.write(f":source:level:auto {value}")

    def disconnect(self) -> None:
        """ """
        self.state = "off"
        self.handle.close()
