from typing import Any, ClassVar
from collections.abc import MutableMapping
from qcrew.helpers import logger
import yaml
from qm import qua
import numpy as np
import copy


class Parametrized(MutableMapping):

    # class variable defining the default parameter set for Parametrized objects
    # subclasses to override
    _parameters = set()

    def __init__(self):
        self._parameters = set(self.__dict__.keys())

    @property
    def parameters(self) -> dict[str, Any]:

        param_dict = dict()
        for param in self._parameters:

            try:
                param_value = getattr(self, param)
            except AttributeError:
                cls_ = type(self).__name__  # get subclass name
                logger.error(f"Parameter '{param}' must be an attribute of {cls_}")

            else:  # get params recursively if Parametrized objects found in param_value
                if isinstance(param_value, Parametrized):
                    param_dict[param] = param_value.parameters
                elif isinstance(param_value, (list, tuple, set, frozenset)):
                    param_list = list()
                    for value in param_value:
                        if isinstance(value, Parametrized):
                            param_list.append(value.parameters)
                        elif value in {int, bool, float, qua.fixed, np.ndarray}:
                            param_list.append(value.__name__)
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

                elif param_value in {int, bool, float, qua.fixed, np.ndarray}:
                    param_dict[param] = param_value.__name__
                else:
                    param_dict[param] = param_value
        return param_dict

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        if key in self.__dict__:
            del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self._parameters)

    def _keytransform(self, key):
        return key

    def __str__(self):
        return yaml.dump(self.parameters, sort_keys=False, default_style=False)


if __name__ == "__main__":

    class Param(Parametrized):
        def __init__(self, name):
            self.name = name
            self.a = 99
            self.type = int
            super().__init__()

    class Test(Parametrized):
        def __init__(self):
            self.name = "test_name"
            self.length = 14
            self.test_list = ["a", "b"]
            self.param_list = [Param("parameter1"), Param("parameter2")]
            self.test_tupe = ("tuple_a", "tuple_b")
            self.test_set = {"set_a", "set_b"}
            self.test_dict = {"I": Param("I"), "Q": Param("Q")}
            super().__init__()

    a = Test()
    print("===================")
    print(a.parameters)
    print("===================")
    print(a)
    print("===================")
    print(a.get("name"))
