"""
This module defines base classes for encapsulating instruments in qcrew's lab.
TODO WRITE DOCUMENTATION
"""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, fields
from typing import Any, NoReturn

STATUS_DICT = {"connected": False, "running": False, "staged": False}


@dataclass
class Instrument(ABC):
    status: dict[str, bool] = field(
        default_factory=STATUS_DICT.copy, init=False, compare=False
    )

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        pass

    @property
    def yaml_map(self) -> dict[str, Any]:
        init_fields_filter = filter(lambda f: f.init, fields(self))
        init_field_names = tuple(map(lambda f: f.name, init_fields_filter))
        yaml_map = {k: v for (k, v) in asdict(self).items() if k in init_field_names}
        return yaml_map


@dataclass
class PhysicalInstrument(Instrument):
    id: Any  # OK to shadow built-in `id` as `PhysicalInstrument` ids ought to be unique
    _handle: Any = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        self._connect()
        self._initialize()

    @abstractmethod
    def _connect(self) -> NoReturn:
        pass

    @abstractmethod
    def _initialize(self) -> NoReturn:
        pass

    @abstractmethod
    def disconnect(self) -> NoReturn:
        pass
