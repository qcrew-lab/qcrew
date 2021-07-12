""" """

import inspect
from pathlib import Path
from typing import Any, Type, TypeVar

import numpy
import yaml

from qcrew.helpers import logger


def _sci_not_representer(dumper, value) -> yaml.ScalarNode:
    """ """
    # use scientific notation if abs(value) >= threshold
    threshold = 1e3  # based on the feeling that values > 1e3 are better read in sci not
    yaml_float_tag = "tag:yaml.org,2002:float"
    value_in_sci_not = f"{value:E}" if abs(value) >= threshold else str(value)
    return dumper.represent_scalar(yaml_float_tag, value_in_sci_not)


class YamlableMetaclass(type):
    """ """

    def __init__(cls, name, bases, kwds) -> None:
        """ """
        super(YamlableMetaclass, cls).__init__(name, bases, kwds)
        cls.yaml_tag = name  # set a consistent format for subclass yaml tags
        # register safe loader and safe dumper
        cls.yaml_loader, cls.yaml_dumper = yaml.SafeLoader, yaml.SafeDumper
        # custom constructor and representer for Yamlable objects
        cls.yaml_loader.add_constructor(cls.yaml_tag, cls.from_yaml)
        cls.yaml_dumper.add_representer(cls, cls.to_yaml)
        # customise dumper to represent float values in scientific notation
        cls.yaml_dumper.add_representer(float, _sci_not_representer)
        cls.yaml_dumper.add_multi_representer(numpy.floating, _sci_not_representer)

    def __repr__(cls) -> str:
        """ """
        return f"<class '{cls.__name__}'>"


class Yamlable(metaclass=YamlableMetaclass):
    """ """

    @property
    def yaml_map(self) -> dict[str, Any]:
        """ """
        init_args_dict = inspect.signature(self.__init__).parameters
        try:
            yaml_map = {arg: getattr(self, arg) for arg in init_args_dict}
        except AttributeError as e:
            logger.exception("All arguments to Yamlable __init__() must be attributes")
            raise SystemExit("Failed to create yaml_map, exiting...") from e
        else:
            logger.success(f"Created .yaml mapping for {type(self).__name__}")
            return yaml_map

    @classmethod
    def from_yaml(cls, loader, node):
        """ """
        parameters = loader.construct_mapping(node, deep=True)
        logger.info(f"Loading {cls.__name__} from .yaml")
        try:
            return cls(**parameters)
        except TypeError as te:
            logger.error(f"{cls.__name__} 'yaml_map' is incompatible with __init__()")
            raise SystemExit(f"Failed to load {cls.__name__}, exiting...") from te
        except yaml.YAMLError as ye:
            logger.exception("Yaml error encountered while loading from config")
            raise SystemExit(f"Failed to load {cls.__name__}, exiting...") from ye

    @classmethod
    def to_yaml(cls, dumper, data) -> yaml.MappingNode:
        """ """
        logger.info(f"Dumping {cls.__name__} to .yaml")
        try:
            return dumper.represent_mapping(data.yaml_tag, data.yaml_map)
        except yaml.YAMLError as ye:
            logger.exception("Yaml error encountered while saving to config")
            raise SystemExit(f"Failed to save {cls.__name__}, exiting...") from ye


def load(path: Path):
    """ """
    with path.open(mode="r") as file:
        return yaml.safe_load(file)


def save(yaml_map, path: Path, mode: str = "w") -> None:
    """ """
    with path.open(mode=mode) as file:
        yaml.safe_dump(yaml_map, file, sort_keys=False)
