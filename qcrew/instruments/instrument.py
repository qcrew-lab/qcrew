"""
This module defines abstract base classes for encapsulating instruments in qcrew's lab.
TODO WRITE DOCUMENTATION
"""
from abc import abstractmethod
from dataclasses import dataclass, field, InitVar
from typing import Any, NoReturn

from qcrew.helpers import Yamlable

STATUS_DICT = {"staged": False, "connected": False, "running": False}  # explain these


@dataclass
class Instrument(Yamlable):
    _status: dict[str, Any] = field(default_factory=STATUS_DICT.copy, init=False)
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
