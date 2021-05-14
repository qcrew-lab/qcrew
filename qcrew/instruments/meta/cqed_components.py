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
    # class variable defining the default offsets dictionary of IQMixer objects
    _default_offsets_dict: ClassVar[dict[str, float]] = {
        "I": 0.0,  # DC offset applied by a OPX AO port to the I port of the IQMixer
        "Q": 0.0,  # DC offset applied by a OPX AO port to the Q port of the IQMixer
        "G": 0.0,  # offset used by OPX to correct the gain imbalance of the IQMixer
        "P": 0.0,  # offset used by OPX to correct the phase imbalance of the IQMixer
    }

    # stores statuses of this instance
    _status: dict[str, Any] = field(default_factory=_status_dict.copy, init=False)

    # getters for this instance's parameterss
    name: str = field(default=None)
    offsets: dict[str, float] = field(default_factory=_default_offsets_dict.copy)

    def __post_init__(self) -> NoReturn:
        """ """
        logger.info(
            "Created {} with name: {}, offsets: {} ",
            type(self).__name__,
            self.name,
            self.offsets,
        )
        if self.name is None:
            logger.warning("{} name initialized as {}", type(self).__name__, None)
        if self.offsets == self._default_offsets_dict:
            logger.warning("{} initialized with default offsets", type(self).__name__)


@dataclass
class QuantumElement(Instrument):
    """ """

    # class variable defining the parameter set for QuantumElement objects
    _parameters: ClassVar[frozenset[str]] = frozenset(
        [
            "name",  # a unique name describing the QuantumElement
            "lo_freq",  # frequency of local oscillator driving the QuantumElement
            "lo_power",  # output power of local oscillator driving the QuantumElement
            "int_freq",  # intermediate frequency driving the QuantumElement
            "ports",  # input and output ports of the QuantumElement
            "mixer",  # the IQMixer object associated with the QuantumElement
            "operations",  # the operations that can be performed on the QuantumElement
        ]
    )

    name: str
    lo: LabBrick
    int_freq: Union[int, float]
    ports: dict[str, int]
    mixer: IQMixer = field(default=None)
    # operations: dict  TODO operations is a dict of str keys and pulse values

    def _validate_parameters(self) -> NoReturn:
        """ """
        try:
            self._validate_lo()
            self._validate_mixer()
        except TypeError:
            logger.exception("Failed to validate {} parameters", self.name)
            raise
        else:
            logger.success(
                "Created {} with name: {}, get current state by calling .parameters",
                type(self).__name__,
                self.name,
            )

    def _validate_lo(self) -> NoReturn:
        """ """
        if not isinstance(self.lo, LabBrick):
            raise TypeError("Expect lo of {}, got {}".format(LabBrick, type(self.lo)))

    def _validate_mixer(self) -> NoReturn:
        """ """
        if self.mixer is None:
            logger.warning("{} initialized without an {}", self.name, IQMixer.__name__)
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

    @property  # lo_power getter
    def lo_power(self) -> float:
        """ """
        return self.lo.power

    @lo_power.setter
    def lo_power(self, new_power: Union[int, float]) -> NoReturn:
        """ """
        self.lo.power = new_power


@dataclass
class Qubit(QuantumElement):
    """ """

    # define default operations dict

    def __post_init__(self) -> NoReturn:
        """ """
        self._validate_parameters()


@dataclass
class ReadoutResonator(QuantumElement):
    """ """

    # define default operations dict

    time_of_flight: int = field(default=180)
    smearing: int = field(default=0)

    def __post_init__(self) -> NoReturn:
        """ """
        self._validate_parameters()
        if self.time_of_flight == 180:
            logger.warning(
                "{} {} time of flight set to default value {}ns",
                type(self).__name__,
                self.name,
                self.time_of_flight,
            )
        if self.smearing == 0:
            logger.warning(
                "{} {} smearing set to default value {}ns",
                type(self).__name__,
                self.name,
                self.smearing,
            )


@dataclass
class QuantumDevice(Instrument):
    """ """

    # class variable defining the status keys for QuantumDevice objects
    _status_dict: ClassVar[dict[str, bool]] = {"staged": False, "measuring": False}
    # class variable defining the parameter set for QuantumDevice objects
    _parameters: ClassVar[frozenset[str]] = frozenset(
        [
            "name",  # a unique name describing the QuantumDevice
            "elements",  # set of QuantumElements that are part of the QuantumDevice
        ]
    )

    name: str
    elements: set[QuantumElement]

    def __post_init__(self) -> NoReturn:
        """ """
        try:
            self._validate_elements()
        except TypeError:
            logger.exception("Failed to validate {} parameters", self.name)
            raise
        else:
            logger.success(
                "Created {} with name: {}, get current state by calling .parameters",
                type(self).__name__,
                self.name,
            )

    def _validate_elements(self):
        """ """
        if not isinstance(self.elements, set):
            raise TypeError(
                "Expect elements container of {}, got {}".format(
                    set, type(self.elements)
                )
            )

        for element in self.elements:
            if not isinstance(element, QuantumElement):
                raise TypeError(
                    "Expect element of {}, got {}".format(QuantumElement, type(element))
                )
