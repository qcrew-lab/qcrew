""" """

from typing import Any, ClassVar

from qcrew.helpers import logger
from qcrew.helpers.yamlizer import Yamlable


class Parametrized(Yamlable):
    """ """

    # class variable defining the default parameter set for Parametrized objects
    _parameters: ClassVar[set[str]] = set()  # subclasses to override

    @property
    def parameters(self) -> dict[str, Any]:
        """ """
        param_dict = dict()
        for param in self._parameters:
            try:
                param_value = getattr(self, param)
            except AttributeError as e:
                cls_ = type(self).__name__  # get subclass name
                logger.exception(f"Parameter '{param}' must be an attribute of {cls_}")
                raise SystemExit("Failed to get parameters, exiting...") from e
            else:
                if isinstance(param_value, Parametrized):
                    param_dict[param] = param_value.parameters  # get params recursively
                else:
                    param_dict[param] = param_value
        return param_dict

    @parameters.setter
    def parameters(self, new_parameters: dict[str, Any]) -> None:
        """ """
        # TODO error handling and logging
        for param, value in new_parameters.items():
            if param in self._parameters:
                setattr(self, param, value)
