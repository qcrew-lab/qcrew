"""
This module supports serializing and deserializing of those Python classes in qcrew
that inherit from Yamlable and implement the `yaml_map` property.
TODO WRITE DOCUMENTATION
"""
from abc import ABCMeta, abstractmethod
import yaml

YAML_TAG_PREFIX = u"1"


# use scientific notation if abs(value) >= threshold
def sci_not_representer(dumper, value):
    """ """
    threshold = 1e3
    yaml_float_tag = u"tag:yaml.org,2002:float"
    value_in_sci_not = "{:.2e}".format(value) if abs(value) >= threshold else str(value)
    return dumper.represent_scalar(yaml_float_tag, value_in_sci_not)


# lists must be always represented in flow style, not block style
def sequence_representer(dumper, value):
    """ """
    yaml_seq_tag = u"tag:yaml.org,2002:seq"
    return dumper.represent_sequence(yaml_seq_tag, value, flow_style=True)


class YamlableMetaclass(ABCMeta):
    """ """

    def __init__(cls, name, bases, kwds):
        super(YamlableMetaclass, cls).__init__(name, bases, kwds)

        # set a consistent format for subclass yaml tags
        cls.yaml_tag = YAML_TAG_PREFIX + name

        # register loader(s) and dumper(s)
        yaml.SafeLoader.add_constructor(cls.yaml_tag, cls.from_yaml)
        yaml.SafeDumper.add_representer(cls, cls.to_yaml)
        # custom dumper for representing float in scientific notation
        yaml.SafeDumper.add_representer(float, sci_not_representer)
        # custom dumper for always representing tuples and lists in flow style
        yaml.SafeDumper.add_representer(list, sequence_representer)


class Yamlable(metaclass=YamlableMetaclass):
    """ """

    @property
    @abstractmethod
    def yaml_map(self):
        """ """

    @classmethod
    def from_yaml(cls, loader, node):
        """ """
        yaml_map = loader.construct_mapping(node)
        return cls(**yaml_map)

    @classmethod
    def to_yaml(cls, dumper, data):
        """ """
        return dumper.represent_mapping(data.yaml_tag, data.yaml_map)
