""" """
from dataclasses import dataclass, field
from typing import Any, ClassVar, Union

from qcrew.instruments import Instrument, LabBrick


@dataclass
class IQMixer(Instrument):
    """ """

    # class variables defining default status dict and param set for IQMixer objects
    _status_dict: ClassVar[dict[str, bool]] = {"staged": False, "tuned": False}
    _parameters_set: ClassVar[set[str]] = {"name", "offsets"}

    # class variable defining the dictionary of offsets for IQMixer objects
    _iqmixer_offsets_dict: ClassVar[dict[str, float]] = {
        "i": None,  # DC offset applied by a OPX AO port to the I port of the IQMixer
        "q": None,  # DC offset applied by a OPX AO port to the Q port of the IQMixer
        "g": None,  # offset used by OPX to correct the gain imbalance of the IQMixer
        "p": None,  # offset used by OPX to correct the phase imbalance of the IQMixer
    }

    # stores statuses and parameters of this instance
    _status: dict[str, Any] = field(default_factory=_status_dict.copy, init=False)
    _parameters: dict[str, Any] = field(
        default_factory=_parameters_set.copy, init=False, repr=False
    )

    # to store name and offsets of this IQMixer instance
    name: str = field(default=None)
    offsets: dict[str, float] = field(default_factory=_iqmixer_offsets_dict.copy)


@dataclass
class Qubit(Instrument):
    """ """

    # class variables defining default parameter set for IQMixer objects
    _parameters_set: ClassVar[set[str]] = {
        "name",
        "int_freq",
        "lo",
        "ports",
        "mixer",
        "operations",
    }

    # class variable defining the dictionary of ports for Qubit objects
    _qubit_ports_dict: ClassVar[dict[str, int]] = {
        "i": None,  # OPX AO port connected to the I port of this qubit's IQMixer
        "q": None,  # OPX AO port connected to the Q port of this qubit's IQMixer
        "in": None,  # single OPX AO port connected to this qubit
    }

    # stores parameters of this instance
    _parameters: dict[str, Any] = field(
        default_factory=_parameters_set.copy, init=False, repr=False
    )

    name: str
    int_freq: Union[int, float]
    lo: LabBrick
    ports: dict[str, int] = field(default_factory=_qubit_ports_dict.copy)
    mixer: IQMixer = field(default=None)
    # operations is a dict of str keys and pulse values


@dataclass
class ReadoutResonator(Instrument):
    """ """

    # qubit params AND tof, smearing, ro-related-params


@dataclass
class StorageCavity(Instrument):
    """ """
    # TODO in near future

@dataclass
class QuantumDevice(Instrument):
    """ """
    # container class, sets statuses for all meta-instruments it is composed of
