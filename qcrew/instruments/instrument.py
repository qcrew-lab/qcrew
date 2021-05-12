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

    # class variable defining the default status dict for Instrument objects
    _status_dict: ClassVar[dict[str, bool]] = {"staged": False}

    # subclasses to override these dictionaries as they deem fit
    _status: dict[str, Any] = field(
        default_factory=_status_dict.copy, init=False, repr=False
    )
    _parameters: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    @property
    def status(self) -> dict[str, Any]:
        """ """
        # condition - self._status must represent current status
        # subclasses are responsible for tracking current status
        return self._status

    @property
    def parameters(self) -> dict[str, Any]:
        """ """
        # condition - every key in self._parameters must be an instance attribute
        # subclasses are responsible for defining the attribute getter
        return {k: getattr(self, k) for k in self._parameters}


@dataclass
class PhysicalInstrument(Instrument):
    """ """

    # class variable defining the default status dict for PhysicalInstrument objects
    _status_dict: ClassVar[dict[str, bool]] = {
        "staged": False,
        "connected": False,
        "running": False,
    }

    # stores statuses of this instance
    _status: dict[str, Any] = field(default_factory=_status_dict.copy, init=False)

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
