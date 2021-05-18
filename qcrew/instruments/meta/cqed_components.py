""" """
from dataclasses import asdict, dataclass, field, InitVar
from typing import ClassVar, NoReturn, Union

from qcrew.helpers import logger
"""from qcrew.helpers.pulsemaker import (
    Pulse,
    DEFAULT_CW_PULSE,
    DEFAULT_GAUSSIAN_PULSE,
    DEFAULT_READOUT_PULSE,
)"""
from qcrew.instruments import Instrument, LabBrick



@dataclass(repr=False, eq=False)
class QuantumElementPorts:
    """ """

    # pylint: disable=invalid-name
    # these names have specific meanings that are well understood by qcrew

    # OPX AO port connected to I port of this QuantumElement's IQMixer
    I: int = field(default=None)
    # OPX AO port connected to Q port of this QuantumElement's IQMixer
    Q: int = field(default=None)
    # single OPX AO port connected to this QuantumElement
    inp: int = field(default=None)
    # OPX AI port that the output of this QuantumElement is fed to
    out: int = field(default=None)

    # pylint: enable=invalid-name

    @property  # has_mix_inputs getter
    def has_mix_inputs(self) -> bool:
        """ """
        return self.I is not None and self.Q is not None


#@dataclass
class QuantumElement(Instrument):
    """ """

    # class variable defining the parameter set for QuantumElement objects
    _parameters: ClassVar[frozenset] = frozenset()  # subclasses to override

    def _create_ports(self, initial_ports: dict[str, int]) -> QuantumElementPorts:
        """ """
        is_valid_ports = (
            isinstance(initial_ports, dict)
            and set(initial_ports) in self._ports_keysets
        )

        if is_valid_ports:
            return QuantumElementPorts(**initial_ports)
        elif not isinstance(initial_ports, dict):
            logger.exception(
                "Expected ports of {}, got {}", dict[str, int], type(initial_ports)
            )
            raise TypeError("ports must be {}".format(dict))
        elif set(initial_ports) not in self._ports_keysets:
            logger.exception(
                "Set of keys in ports must be equal to one of {}",
                [set(keyset) for keyset in self._ports_keysets],
            )
            raise ValueError("Invalid keys found in ports")

    def _check_parameters(self) -> NoReturn:
        """ """
        try:
            self._check_lo()
            self._check_mixer()
            self._check_operations()
        except TypeError:
            logger.exception(
                "Failed to validate {} {} parameters", type(self).__name__, self.name
            )
            raise
        else:
            logger.info(
                "Created {} with name: {}, get current state by calling .parameters",
                type(self).__name__,
                self.name,
            )

    def _check_lo(self) -> NoReturn:
        """ """
        if not isinstance(self.lo, LabBrick):
            raise TypeError("Expect lo of {}, got {}".format(LabBrick, type(self.lo)))

    def _check_mixer(self) -> NoReturn:
        """ """
        if self._ports.has_mix_inputs:
            if self.mixer is None:
                logger.info(
                    "{} {} with mix inputs initialized without {}, creating one now...",
                    type(self).__name__,
                    self.name,
                    IQMixer.__name__,
                )
                self.mixer = IQMixer(name=IQMixer.default_name_prefix + self.name)
            elif not isinstance(self.mixer, IQMixer):
                raise TypeError(
                    "Expect mixer of {}, got {}".format(IQMixer, type(self.mixer))
                )
        else:
            if self.mixer is not None:
                self.mixer = None
                logger.warning(
                    "{} {} with single input initialized with {}, setting it to {}",
                    type(self).__name__,
                    self.name,
                    IQMixer.__name__,
                    None,
                )

    def _check_operations(self) -> NoReturn:
        """ """
        if not isinstance(self.operations, dict):
            raise TypeError(
                "Expect operations of {}, got {}".format(
                    dict[str, Pulse], type(self.operations)
                )
            )

        for name, pulse in self.operations.items():
            if not isinstance(name, str):
                raise TypeError(
                    "Expect operation name of {}, got {}".format(str, type(name))
                )
            if not isinstance(pulse, Pulse):
                raise TypeError(
                    "Expect operation of {}, got {}".format(Pulse, type(pulse))
                )
            if not pulse.has_valid_waveforms:
                raise ValueError("Operation {} has invalid waveforms".format(name))
            if self._ports.has_mix_inputs and pulse.has_single_waveform:
                raise ValueError(
                    "{} with mix inputs has operation {} with single waveform".format(
                        type(self).__name__, name
                    )
                )

    @property  # has_valid_operations getter
    def has_valid_operations(self) -> bool:
        try:
            self._check_operations()
        except TypeError:
            logger.error(
                "{} {} operations, must be {}",
                type(self).__name__,
                self.name,
                dict[str, Pulse],
            )
            return False
        except ValueError:
            logger.error(
                "{} {} has an operation with invalid waveforms",
                type(self).__name__,
                self.name,
            )
            return False
        else:
            return True

    @property  # name getter
    def name(self) -> str:
        return self._name

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

    @property  # ports getter
    def ports(self) -> dict[str, int]:
        """ """
        return {k: v for (k, v) in asdict(self._ports).items() if v is not None}


@dataclass
class Qubit(QuantumElement):
    """ """

    # class variable defining the parameter set for Qubit objects
    _parameters: ClassVar[frozenset[str]] = frozenset(
        [
            "name",  # a unique name describing the Qubit
            "lo_freq",  # frequency of local oscillator driving the Qubit
            "lo_power",  # output power of local oscillator driving the Qubit
            "int_freq",  # intermediate frequency driving the Qubit
            "ports",  # input QuantumElementPorts of the Qubit
            "mixer",  # the IQMixer (if any) associated with the Qubit
            "operations",  # operations that can be performed on the Qubit
        ]
    )

    # class variable defining valid keyset(s) of ports of Qubit objects
    _ports_keysets: ClassVar[frozenset[frozenset[str]]] = frozenset(
        [
            frozenset(["inp"]),
            frozenset(["I", "Q"]),
        ]
    )

    # class variable defining the default operations for Qubit objects
    _default_operations: ClassVar[dict[str, Pulse]] = {
        "CW": DEFAULT_CW_PULSE,
        "gaussian": DEFAULT_GAUSSIAN_PULSE,
    }

    name: InitVar[str]
    lo: LabBrick
    int_freq: Union[int, float]
    mixer: IQMixer = field(default=None)  # will be created based on ports
    operations: dict[str, Pulse] = field(default_factory=_default_operations.copy)

    ports: InitVar[dict[str, int]]
    operations: dict[str, Pulse] = field(default_factory=_default_operations.copy)

    def __post_init__(self, name: str, ports: dict[str, int]) -> NoReturn:
        """ """
        self._name = self._
        self._ports = self._create_ports(ports)
        self._check_parameters()


@dataclass
class ReadoutResonator(QuantumElement):
    """ """

    # class variable defining the parameter set for ReadoutResonator objects
    _parameters: ClassVar[frozenset[str]] = frozenset(
        [
            "name",  # a unique name describing the ReadoutResonator
            "lo_freq",  # frequency of local oscillator driving the ReadoutResonator
            "lo_power",  # output power of local oscillator driving the ReadoutResonator
            "int_freq",  # intermediate frequency driving the ReadoutResonator
            "ports",  # input and output QuantumElementPorts of the ReadoutResonator
            "mixer",  # the IQMixer (if any) associated with the ReadoutResonator
            "operations",  # operations that can be performed on the ReadoutResonator
            "time_of_flight",  # as defined in the QM configuration specification
            "smearing",  # as defined in the QM configuration specification
        ]
    )

    # class variable defining valid keyset(s) of ports of ReadoutResonator objects
    _ports_keysets: ClassVar[frozenset[frozenset[str]]] = frozenset(
        [
            frozenset(["inp", "out"]),
            frozenset(["I", "Q", "out"]),
        ]
    )

    # class variable defining the default name for Qubit objects
    _default_name: ClassVar[str] = "rr"

    # class variable defining the default operations for Qubit objects
    _default_operations: ClassVar[dict[str, Pulse]] = {
        "CW": DEFAULT_CW_PULSE,
        "readout": DEFAULT_READOUT_PULSE,
    }

    ports: InitVar[dict[str, int]]
    operations: dict[str, Pulse] = field(default_factory=_default_operations.copy)
    time_of_flight: int = field(default=180)
    smearing: int = field(default=0)

    def __post_init__(self, name: str, ports: dict[str, int]) -> NoReturn:
        """ """
        self._name = name if isinstance(name, str) else self._default_name
        self._ports = self._create_ports(ports)
        if self.time_of_flight == 180:
            logger.warning(
                "No {} {} time of flight given, set to default value {}ns",
                type(self).__name__,
                self.name,
                self.time_of_flight,
            )
        if self.smearing == 0:
            logger.warning(
                "No {} {} smearing given, set to default value {}ns",
                type(self).__name__,
                self.name,
                self.smearing,
            )
        self._check_parameters()


@dataclass
class QuantumDevice(Instrument):
    """ """

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
            self._check_elements()
        except TypeError:
            logger.exception(
                "{} {} parameter check failed", type(self).__name__, self.name
            )
            raise
        else:
            logger.info(
                "Created {} with name: {}, get current state by calling .parameters",
                type(self).__name__,
                self.name,
            )

    def _check_elements(self) -> NoReturn:
        """ """
        if not isinstance(self.elements, set):
            raise TypeError(
                "Expect elements container of {}, got {}".format(
                    set[QuantumElement], type(self.elements)
                )
            )

        for element in self.elements:
            if not isinstance(element, QuantumElement):
                raise TypeError(
                    "Expect element of {}, got {}".format(QuantumElement, type(element))
                )

    @property  # has_valid_elements getter
    def has_valid_elements(self) -> bool:
        """ """
        try:
            self._check_elements()
        except TypeError:
            logger.warning(
                "Failed to validate {} {} elements", type(self).__name__, self.name
            )
            return False
        else:
            return True
