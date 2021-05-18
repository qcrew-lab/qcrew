""" """
import inspect

import yaml

from qcrew.helpers import logger

# use scientific notation if abs(value) >= threshold
def sci_not_representer(dumper, value):
    """ """
    threshold = 1e3  # arbitrary value
    yaml_float_tag = "tag:yaml.org,2002:float"
    value_in_sci_not = f"{value:.7E}" if abs(value) >= threshold else str(value)
    return dumper.represent_scalar(yaml_float_tag, value_in_sci_not)


# lists must be always represented in flow style, not block style
def sequence_representer(dumper, value):
    """ """
    yaml_seq_tag = "tag:yaml.org,2002:seq"
    return dumper.represent_sequence(yaml_seq_tag, value, flow_style=True)


class YamlableMetaclass(type):
    """ """

    def __init__(cls, name, bases, kwds):
        """ """
        super(YamlableMetaclass, cls).__init__(name, bases, kwds)

        # set a consistent format for subclass yaml tags
        # cls.yaml_tag = YAML_TAG_PREFIX + name
        cls.yaml_tag = name

        # register safe loader and safe dumper
        cls.yaml_loader, cls.yaml_dumper = yaml.SafeLoader, yaml.SafeDumper

        # custom constructor and representer for Yamlable objects
        cls.yaml_loader.add_constructor(cls.yaml_tag, cls.from_yaml)
        cls.yaml_dumper.add_representer(cls, cls.to_yaml)
        # customise dumper to represent float values in scientific notation
        cls.yaml_dumper.add_representer(float, sci_not_representer)
        # customise dumper to represent tuples and lists in flow style
        cls.yaml_dumper.add_representer(list, sequence_representer)


class Yamlable(metaclass=YamlableMetaclass):
    """ """

    @property
    def yaml_map(self):
        """ """
        init_args_dict = inspect.signature(self.__init__).parameters
        try:
            yaml_map = {k: getattr(self, k) for k in init_args_dict}
        except AttributeError:
            logger.exception(f"All __init__ args of Yamlables must also be attributes")
            raise
        else:
            logger.info(f"Created .yaml mapping for {type(self).__name__}")
            return yaml_map

    @classmethod
    def from_yaml(cls, loader, node):
        """ """
        yaml_map = loader.construct_mapping(node)
        logger.info(f"Loading {cls.__name__} from .yaml")
        return cls(**yaml_map)

    @classmethod
    def to_yaml(cls, dumper, data):
        """ """
        logger.info(f"Dumping {cls.__name__} to .yaml")
        return dumper.represent_mapping(data.yaml_tag, data.yaml_map)
