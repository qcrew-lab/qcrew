""" """

import inspect
from pathlib import Path
from typing import Any

import numpy
import yaml

from qcrew.helpers import logger


def load(path: Path):
    """ """
    try:
        with open(path, mode="r") as file:
            return yaml.safe_load(file)
    except AttributeError:
        logger.error("Bad key found in yaml map")
        raise
    except IOError:
        logger.error(f"Unable to find / open a file at {path}")
        raise
    except yaml.YAMLError:
        logger.error(f"Unrecognized yaml tag found in {path.name}")
        raise


def save(yaml_map, path: Path) -> None:
    """ """
    try:
        with open(path, mode="w") as file:
            yaml.safe_dump(yaml_map, file, sort_keys=False)
    except IOError:
        logger.error(f"Unable to find / open a file at {path}")
        raise
    except yaml.YAMLError:
        logger.error("Unrecognized value found in yaml map")
        raise


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
        yaml_map_keys = self._get_yaml_map_keys()
        yaml_map = dict()
        for key in yaml_map_keys:
            try:
                value = getattr(self, key)
            except AttributeError as e:
                logger.exception(f"{key} must be an attribute of {self}")
                raise SystemExit("Failed to create yaml map, exiting...") from e
            else:
                if value is not None:
                    yaml_map[key] = value
        logger.success(f"Created yaml map for {type(self)}")
        return yaml_map

    def _get_yaml_map_keys(self) -> set[str]:
        """ """
        ancestors = inspect.getmro(type(self))  # mro means method resolution order
        all_yaml_map_keys = list()  # of all ancestors
        for ancestor in ancestors:
            init_params = inspect.signature(ancestor.__init__).parameters.values()
            yaml_map_keys = list()  # of this ancestor
            found_kwargs = False
            for param in init_params:
                is_self = param.name == "self"
                is_yaml_map_key = not (is_self or param.kind == param.VAR_POSITIONAL)
                if param.kind == param.VAR_KEYWORD:
                    found_kwargs = True
                elif is_yaml_map_key:
                    yaml_map_keys.append(param.name)
            all_yaml_map_keys = [*yaml_map_keys, *all_yaml_map_keys]  # preserve order
            if not found_kwargs:
                break
        return all_yaml_map_keys

    @classmethod
    def from_yaml(cls, loader, node):
        """ """
        parameters = loader.construct_mapping(node, deep=True)
        logger.info(f"Loading {cls.__name__} from yaml...")
        try:
            return cls(**parameters)
        except TypeError as te:
            logger.error(f"{cls.__name__} yaml map is incompatible with its __init__()")
            raise SystemExit(f"Failed to load {cls.__name__}, exiting...") from te

    @classmethod
    def to_yaml(cls, dumper, data) -> yaml.MappingNode:
        """ """
        logger.info(f"Dumping {cls.__name__} to yaml...")
        return dumper.represent_mapping(data.yaml_tag, data.yaml_map)
