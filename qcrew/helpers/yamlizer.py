""" """

from pathlib import Path
from typing import Any, Type, TypeVar

import yaml

from qcrew.helpers import logger


def _sci_not_representer(dumper, value) -> yaml.ScalarNode:
    """ """
    # use scientific notation if abs(value) >= threshold
    threshold = 1e3  # based on the feeling that values > 1e3 are better read in sci not
    yaml_float_tag = "tag:yaml.org,2002:float"
    value_in_sci_not = f"{value:E}" if abs(value) >= threshold else str(value)
    return dumper.represent_scalar(yaml_float_tag, value_in_sci_not)


def _sequence_representer(dumper, value) -> yaml.SequenceNode:
    """ """
    # lists must be always represented in flow style, not block style
    yaml_seq_tag = "tag:yaml.org,2002:seq"
    return dumper.represent_sequence(yaml_seq_tag, value, flow_style=True)


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
        # customise dumper to represent tuples and lists in flow style
        cls.yaml_dumper.add_representer(list, _sequence_representer)

    def __repr__(cls) -> str:
        """ """
        return f"<class '{cls.__name__}'>"


YamlableType = TypeVar("Yamlable", bound="Yamlable")  # for type hints


class Yamlable(metaclass=YamlableMetaclass):
    """ """

    @classmethod
    def from_yaml(cls: Type[YamlableType], loader, node) -> YamlableType:
        """ """
        parameters = loader.construct_mapping(node)
        logger.info(f"Loading {cls.__name__} from .yaml")
        try:
            return cls(**parameters)
        except TypeError as e:
            logger.error(f"{cls.__name__} 'yaml_map' is incompatible with __init__()")
            raise SystemExit(f"Failed to load {cls.__name__}, exiting...") from e

    @classmethod
    def to_yaml(cls, dumper, data) -> yaml.MappingNode:
        """ """  # TODO error handling
        logger.info(f"Dumping {cls.__name__} to .yaml")
        try:
            return dumper.represent_mapping(data.yaml_tag, data.yaml_map)
        except AttributeError:
            logger.warning("Failed to dump: no 'yaml_map' attribute found")


def load(path: Path) -> Any:
    """ """
    with path.open(mode="r") as file:
        return yaml.safe_load(file)


def save(yamlable: Yamlable, path: Path, mode: str = "a") -> None:
    """ """
    with path.open(mode=mode) as file:
        yaml.safe_dump(yamlable, file, sort_keys=False)
