"""
This module defines abstract base classes for encapsulating instruments in qcrew's lab.
TODO WRITE DOCUMENTATION
"""
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, NoReturn

from qcrew.helpers import Yamlable

STATUS_DICT = {"staged": False}


@dataclass
class Instrument(Yamlable):
    status: dict[str, bool] = field(
        default_factory=STATUS_DICT.copy, init=False, compare=False
    )

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """ """


@dataclass
class PhysicalInstrument(Instrument):
    id: Any  # OK to shadow built-in `id` as `PhysicalInstrument` ids ought to be unique
    _handle: Any = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        self.status.update({"connected": False, "running": False})
        self._connect()
        self._initialize()

    @abstractmethod
    def _connect(self) -> NoReturn:
        """ """

    @abstractmethod
    def _initialize(self) -> NoReturn:
        """ """

    @abstractmethod
    def disconnect(self) -> NoReturn:
        """ """
