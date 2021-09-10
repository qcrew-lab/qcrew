""" """

from typing import Any

from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized
from qcrew.helpers.yamlizer import Yamlizable


class Instrument(Parametrized, Yamlizable):
    """ """

    # pylint: disable=redefined-builtin, intentional shadowing of `id`

    def __init__(self, id, name: str) -> None:
        """ """
        self._id: Any = id
        self._name: str = str(name)

    # pylint: enable=redefined-builtin

    def __repr__(self) -> str:
        """ """
        return f"{self.name}-{self.id}"

    @property  # id getter
    def id(self) -> Any:
        return self._id

    @property  # name getter
    def name(self) -> str:
        return self._name

    def connect(self) -> None:
        """ """
        logger.error("Abstract method must be implemented by subclass(es)")
        raise NotImplementedError("Can't call `connect()` on Instrument instance")

    def _initialize(self) -> None:
        """ """
        logger.error("Abstract method must be implemented by subclass(es)")
        raise NotImplementedError("Can't call `_initialize()` on Instrument instance")

    def disconnect(self) -> None:
        """ """
        logger.error("Abstract method must be implemented by subclass(es)")
        raise NotImplementedError("Can't call `disconnect()` on Instrument instance")
