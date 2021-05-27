""" """

from typing import Any, ClassVar

from qcrew.helpers import logger
from qcrew.helpers.yamlizer import Yamlable

class Paramable(Yamlable):
    """ """

    # class variable defining the default parameter set for Paramable objects
    _parameters: ClassVar[set[str]] = set()  # subclasses to override

    @property
    def parameters(self) -> dict[str, Any]:
        """ """
        param_list = sorted(list(self._parameters))
        param_dict = dict()
        for param in param_list:
            try:
                param_value = getattr(self, param)
            except AttributeError as e:
                cls_ = type(self).__name__
                logger.exception(f"Parameter '{param}' must be an attribute of {cls_}")
                raise SystemExit("Failed to get parameters, exiting...") from e
            else:
                if isinstance(param_value, Paramable):
                    param_dict[param] = param_value.parameters  # get params recursively
                else:
                    param_dict[param] = param_value
        return param_dict

    # TODO parameters.setter
