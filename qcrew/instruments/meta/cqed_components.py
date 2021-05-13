""" """
from dataclasses import dataclass, field
from typing import Any, ClassVar, NoReturn, Union

from qcrew.helpers import logger
from qcrew.instruments import Instrument, LabBrick


@dataclass
class IQMixer(Instrument):
    """ """

    # class variable defining the status keys for IQMixer objects
    _status_dict: ClassVar[dict[str, bool]] = {"staged": False, "tuned": False}
    # class variable defining the parameter set for IQMixer objects
    _parameters: ClassVar[frozenset[str]] = frozenset(["name", "offsets"])
    # class variable defining the keys of the offsets dictionary of IQMixer objects
    _offsets_keys: ClassVar[frozenset[str]] = frozenset(["I", "Q", "G", "P"])

    # stores statuses of this instance
    _status: dict[str, Any] = field(default_factory=_status_dict.copy, init=False)

    # getters for this instance's parameterss
    name: str
    offsets: dict[str, float]

    def __post_init__(self) -> NoReturn:
        """ """
        try:
            self._validate_offsets_keys()
        except (TypeError, ValueError):
            logger.exception("Failed to validate {} offsets", self.name)
            raise
        else:
            logger.success(
                "Created {} with name: {}, offsets: {} ",
                type(self).__name__,
                self.name,
                self.offsets,
            )

    def _validate_offsets_keys(self) -> NoReturn:
        """ """
        if not isinstance(self.offsets, dict):
            raise TypeError(
                "offsets must be of {}, not {}".format(dict, type(self.offsets))
            )
        elif not self.offsets:
            logger.warning("{} initialized with no offsets", type(self).__name__)
        elif not set(self.offsets).issubset(self._offsets_keys):  # not a subset
            raise ValueError(
                "Expect offset keys from {}, got invalid {}".format(
                    self._offsets_keys, set(self.offsets) - self._offsets_keys
                )
            )
        elif not set(self.offsets) < self._offsets_keys:  # not a proper subset
            logger.warning(
                "{} not initialized with all offsets {}",
                type(self).__name__,
                self._offsets_keys,
            )


@dataclass
class QuantumElement(Instrument):
    """ """

    # class variable defining the parameter set for QuantumElement objects
    _parameters: ClassVar[frozenset[str]] = frozenset(
        [
            "name",  # a unique name describing the QuantumElement
            "lo_freq",  # frequency of the local oscillator driving the QuantumElement
            "int_freq",  # intermediate frequency driving the QuantumElement
            "ports",  # input and output ports of the QuantumElement
            "mixer",  # the IQMixer object associated with the QuantumElement
            "operations",  # the operations that can be performed on the QuantumElement
        ]
    )

    # define valid key combinations of the ports dict of QuantumElement objects
    # this class variable is meant to be overriden by subclasses
    _ports_keys: ClassVar[frozenset[str]] = frozenset()

    name: str
    lo: LabBrick
    int_freq: Union[int, float]
    ports: dict[str, int]
    mixer: IQMixer = field(default=None)
    operations: dict  # TODO operations is a dict of str keys and pulse values

    def _validate_parameters(self):
        try:
            self._validate_lo()
            self._validate_ports_keys()
            self._validate_mixer()
        except (TypeError, ValueError):
            logger.exception("Failed to validate {} parameters", self.name)
            raise
        else:
            logger.success(
                "Created {} with name: {} and supplied parameters",
                type(self).__name__,
                self.name,
            )

    def _validate_lo(self):
        if not isinstance(self.lo, LabBrick):
            raise TypeError("Expect lo of {}, got {}".format(LabBrick, type(self.lo)))

    """def _validate_ports_keys(self):
        if not isinstance(self.ports, dict):
            raise TypeError(
                "ports must be of {}, not {}".format(dict, type(self.offsets))
            )"""

    def _validate_mixer(self):
        if self.mixer is None:
            logger.warning("{} not initialized with a mixer", self.name)
        elif not isinstance(self.mixer, IQMixer):
            raise TypeError(
                "Expect mixer of {}, got {}".format(IQMixer, type(self.mixer))
            )

    @property  # lo_freq getter
    def lo_freq(self) -> float:
        """ """
        return self.lo.frequency

    @lo_freq.setter
    def lo_freq(self, new_frequency: Union[int, float]) -> NoReturn:
        """ """
        self.lo.frequency = new_frequency


@dataclass
class Qubit(Instrument):
    """ """

    # define valid key combinations of the ports dict of Qubit objects
    _ports_keys: ClassVar[set[str]] = set()

    def __post_init__(self) -> NoReturn:
        """ """
        self._validate_parameters()


@dataclass
class ReadoutResonator(Instrument):
    """ """

    # define valid key combinations of the ports dict of ReadoutResonator objects
    _ports_keys: ClassVar[set[str]] = set()

    # qubit params AND tof, smearing, ro-related-params

    def __post_init__(self) -> NoReturn:
        """ """
        self._validate_parameters()


@dataclass
class QuantumDevice(Instrument):
    """ """

    # container class, sets statuses for all meta-instruments it is composed of
