"""
This module defines base classes for encapsulating instruments in qcrew's lab.
"""
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, NoReturn


class Instrument:
    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        pass

    @property
    @abstractmethod
    def status(self) -> dict[str, bool]:
        pass


@dataclass
class PhysicalInstrument(Instrument):
    uid: Any

    def __post_init__(self):
        self._connect()
        self._initialize()

    @abstractmethod
    def _connect(self) -> Any:
        pass

    @abstractmethod
    def _initialize(self) -> NoReturn:
        pass

    @abstractmethod
    def disconnect(self) -> NoReturn:
        pass
