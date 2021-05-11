"""
This module defines abstract base classes for encapsulating instruments in qcrew's lab.
TODO WRITE DOCUMENTATION
"""
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, NoReturn

from qcrew.helpers import Yamlable


@dataclass
class Instrument(Yamlable):
    """ """

    # class variable defining the dictionary of statuses for Instrument objects
    instrument_status_dict: ClassVar[dict[str, bool]] = {
        "staged": False,
        "connected": False,
        "running": False,
    }

    _status: dict[str, Any] = field(  # to store statuses of this Instrument instance
        default_factory=instrument_status_dict.copy, init=False
    )

    _parameters: dict[str, Any] = field(default_factory=dict, init=False)

    @property
    def status(self) -> dict[str, Any]:
        """ """
        # condition - self._status must represent current status
        return self._status

    @property
    def parameters(self) -> dict[str, Any]:
        """ """
        # condition - every key in self._parameters must be an instance attribute
        return {k: getattr(self, k) for k in self._parameters}


@dataclass
class PhysicalInstrument(Instrument):
    """ """

    id: Any  # OK to shadow built-in `id` as instrument ids ought to be unique

    @abstractmethod
    def _connect(self) -> NoReturn:
        """ """

    @abstractmethod
    def _initialize(self, *initial_parameters) -> NoReturn:
        """ """

    @abstractmethod
    def disconnect(self) -> NoReturn:
        """ """
