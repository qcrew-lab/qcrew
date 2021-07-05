""" """
from abc import abstractmethod
from typing import Any

from qcrew.helpers.parametrizer import Parametrized


class Instrument(Parametrized):
    """ """

    # pylint: disable=redefined-builtin, intentional shadowing of `id`

    def __init__(self, id) -> None:
        """ """
        self._id: Any = id

    # pylint: enable=redefined-builtin

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__} {self.id}"

    @property  # id getter
    def id(self) -> Any:
        return self._id

    @abstractmethod
    def connect(self) -> None:
        """ """

    @abstractmethod
    def _initialize(self, *initial_parameters) -> None:
        """ """

    @abstractmethod
    def disconnect(self) -> None:
        """ """
