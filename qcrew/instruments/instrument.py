"""
This module defines abstract base classes for encapsulating instruments in qcrew's lab.
TODO WRITE DOCUMENTATION
"""
from abc import abstractmethod
from typing import Any, ClassVar

from qcrew.helpers import logger
from qcrew.helpers.yamlizer import Yamlable


class Instrument(Yamlable):
    """ """

    # class variable defining the default parameter set for Instrument objects
    _parameters: ClassVar[set] = set()  # subclasses to override

    @property
    def parameters(self) -> dict[str, Any]:
        """ """
        param_list = sorted(list(self._parameters))
        param_dict = dict()
        for param in param_list:
            try:
                param_value = getattr(self, param)
            except AttributeError as e:
                logger.exception(f"Instrument parameter '{param}' is not its attribute")
                raise SystemExit("Failed to get parameters, exiting...") from e
            else:
                if isinstance(param_value, Instrument):
                    param_dict[param] = param_value.parameters  # get params recursively
                else:
                    param_dict[param] = param_value
        return param_dict

    # TODO parameters.setter


class PhysicalInstrument(Instrument):
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
    def _connect(self) -> None:
        """ """

    @abstractmethod
    def _initialize(self, *initial_parameters) -> None:
        """ """

    @abstractmethod
    def disconnect(self) -> None:
        """ """
