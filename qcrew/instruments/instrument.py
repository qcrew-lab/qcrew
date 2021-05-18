"""
This module defines abstract base classes for encapsulating instruments in qcrew's lab.
TODO WRITE DOCUMENTATION
"""
from abc import abstractmethod
from typing import Any, ClassVar, NoReturn

from qcrew.helpers.yamlizer import Yamlable


class Instrument(Yamlable):
    """ """

    # class variable defining the default parameter set for Instrument objects
    _parameters: ClassVar[frozenset] = frozenset()  # subclasses to override

    @property
    def parameters(self) -> dict[str, Any]:
        """ """
        # condition - every key in self._parameters must be an instance attribute
        # subclasses are responsible for defining the attribute getter
        return {param: getattr(self, param) for param in self._parameters}

    # TODO parameters.setter


class PhysicalInstrument(Instrument):
    """ """

    # pylint: disable=redefined-builtin, intentional shadowing of `id`

    def __init__(self, id) -> None:
        """ """
        self.id: Any = id

    # pylint: enable=redefined-builtin

    @abstractmethod
    def _connect(self) -> NoReturn:
        """ """

    @abstractmethod
    def _initialize(self, *initial_parameters) -> NoReturn:
        """ """

    @abstractmethod
    def disconnect(self) -> NoReturn:
        """ """
