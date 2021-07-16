""" """

from typing import Any, ClassVar

from qcrew.helpers import logger


class Parametrized:
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
            except AttributeError:
                cls_ = type(self).__name__  # get subclass name
                logger.error(f"Parameter '{param}' must be an attribute of {cls_}")
                raise
            else:  # get params recursively if Parametrized objects found in param_value
                if isinstance(param_value, Parametrized):
                    param_dict[param] = param_value.parameters
                elif isinstance(param_value, (list, tuple, set, frozenset)):
                    param_list = list()
                    for value in param_value:
                        if isinstance(value, Parametrized):
                            param_list.append(value.parameters)
                        else:
                            param_list.append(value)
                    param_dict[param] = param_list
                elif isinstance(param_value, dict):
                    nested_param_dict = dict()
                    for key, value in param_value.items():
                        if isinstance(value, Parametrized):
                            nested_param_dict[key] = value.parameters
                        else:
                            nested_param_dict[key] = value
                        param_dict[param] = nested_param_dict
                else:
                    param_dict[param] = param_value
        return param_dict
