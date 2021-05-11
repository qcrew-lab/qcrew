""" """
from dataclasses import dataclass, field
from typing import Any, ClassVar, Union

from qcrew.instruments import Instrument, LabBrick


@dataclass
class IQMixer:
    """ """

    # class variable defining the dictionary of offsets for IQMixer objects
    iqmixer_offsets_dict: ClassVar[dict[str, float]] = {
        "i": None,  # DC offset applied by a OPX AO port to the I port of the IQMixer
        "q": None,  # DC offset applied by a OPX AO port to the Q port of the IQMixer
        "g": None,  # offset used by OPX to correct the gain imbalance of the IQMixer
        "p": None,  # offset used by OPX to correct the phase imbalance of the IQMixer
    }

    name: str = field(default=None, init=False)
    offsets: dict[str, float] = field(  # to store offsets of this IQMixer instance
        default_factory=iqmixer_offsets_dict.copy, init=False
    )


@dataclass
class Qubit(Instrument):
    """ """

    name: str
    lo: LabBrick
    mixer: IQMixer
    int_freq: Union[int, float]
    # ports named tuple
    # operations is a dict of str keys and pulse values


@dataclass
class ReadoutResonator(Instrument):
    """ """
    # qubit params AND tof, smearing, ro-related-params

@dataclass
class StorageCavity(Instrument):
    """ """


@dataclass
class QuantumDevice(Instrument):
    """ """
