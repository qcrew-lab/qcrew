"""
TODO write proper docu
TODO refactor param checks & logging with DRY
"""
from dataclasses import asdict, dataclass, field, InitVar
from typing import ClassVar, NoReturn, Union

from qcrew.helpers import logger
from qcrew.helpers.pulsemaker import (
    Pulse,
    DEFAULT_CW_PULSE,
    DEFAULT_GAUSSIAN_PULSE,
    DEFAULT_READOUT_PULSE,
)
from qcrew.instruments import Instrument, LabBrick


@dataclass(repr=False, eq=False)
class IQMixerOffsets:
    """ """

    # class variable defining the keyset of the offsets of IQMixer objects
    keyset: ClassVar[frozenset[str]] = frozenset(["I", "Q", "G", "P"])

    # pylint: disable=invalid-name
    # these names have specific meanings that are well understood by qcrew

    # DC offset applied by a OPX AO port to the I port of the IQMixer
    I: float = field(default=0.0)
    # DC offset applied by a OPX AO port to the Q port of the IQMixer
    Q: float = field(default=0.0)
    # offset used by OPX to correct the gain imbalance of the IQMixer
    G: float = field(default=0.0)
    # offset used by OPX to correct the phase imbalance of the IQMixer
    P: float = field(default=0.0)

    # pylint: enable=invalid-name

    def update(self, offset_key: str, new_value: float) -> NoReturn:
        """ """
        if hasattr(self, offset_key) and isinstance(new_value, float):
            setattr(self, offset_key, new_value)
            logger.success(f"Set IQMixer {offset_key} offset to {new_value}")
        else:
            logger.error(f"Invalid offset key value pair ({offset_key}, {new_value})")


@dataclass(eq=False)
class IQMixer(Instrument):
    """ """

    # class variable defining the parameter set for IQMixer objects
    _parameters: ClassVar[frozenset[str]] = frozenset(["name", "offsets"])
    # class variable defining the naming convention for IQMixer objects
    default_name_prefix: ClassVar[str] = "mixer_"

    # getters for this instance's parameters
    name: str
    offsets: InitVar[dict[str, float]]

    def __post_init__(self, offsets: dict[str, float]) -> NoReturn:
        """ """
        self._offsets = self._create_offsets(offsets)
        logger.info(f"Created IQMixer with name: {self.name}, offsets: {self.offsets}")

    def _create_offsets(self, offsets: dict[str, float]) -> IQMixerOffsets:
        """ """
        valid_keys = IQMixerOffsets.keyset
        if not isinstance(offsets, dict) or not offsets:
            logger.warning("No IQMixer offsets given, setting default values...")
            return IQMixerOffsets()
        elif set(offsets) == valid_keys:  # got all valid offsets
            return IQMixerOffsets(**offsets)
        elif set(offsets) < valid_keys:  # got some valid offsets
            logger.warning("Setting defaults for unspecified IQMixer offsets...")
            return IQMixerOffsets(**offsets)
        else:  # got partially valid offsets dict
            logger.warning("Found invalid IQMixer offset(s) keys, ignoring...")
            valid_offsets = {k: offsets[k] for k in valid_keys if k in offsets}
            return IQMixerOffsets(**valid_offsets)

    # pylint: disable=function-redefined, intentional shadowing of InitVar offsets

    @property  # offsets getter
    def offsets(self) -> dict[str, float]:
        """ """
        return asdict(self._offsets)

    # pylint: enable=function-redefined

    @offsets.setter
    def offsets(self, new_offset: tuple[str, float]) -> NoReturn:
        """ """
        # e.g. of a valid offset setter argument: ("I", 0.25)
        try:
            self._offsets.update(new_offset[0], new_offset[1])
        except (TypeError, KeyError, IndexError):
            valid_keys = set(IQMixerOffsets.keyset)
            logger.exception(f"Expect {tuple[str, float]} with str one of {valid_keys}")
            raise


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
            "mixer",  # the IQMixer object (if any) associated with the QuantumElement
            "operations",  # the operations that can be performed on the QuantumElement
        ]
    )
    # class variable defining the default operations for QuantumElement objects
    _default_operations: ClassVar[dict[str, Pulse]] = {"CW": DEFAULT_CW_PULSE}

    name: str
    lo: LabBrick
    int_freq: Union[int, float]
    mixer: IQMixer = field(default=None)  # will be created based on ports
    operations: dict[str, Pulse] = field(default_factory=_default_operations.copy)

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

    ports: InitVar[dict[str, int]]
    operations: dict[str, Pulse] = field(default_factory=_default_operations.copy)

    def __post_init__(self, ports: dict[str, int]) -> NoReturn:
        """ """
        self._ports = self._create_ports(ports)
        self._check_parameters()


@dataclass
class ReadoutResonator(QuantumElement):
    """ """

    # class variable defining valid keyset(s) of ports of ReadoutResonator objects
    _measure_keysets: ClassVar[frozenset[frozenset[str]]] = frozenset(
        [
            frozenset(["inp", "out"]),
            frozenset(["I", "Q", "out"]),
        ]
    )

    # class variable defining the default operations for Qubit objects
    _default_operations: ClassVar[dict[str, Pulse]] = {
        "CW": DEFAULT_CW_PULSE,
        "readout": DEFAULT_READOUT_PULSE,
    }

    ports: InitVar[dict[str, int]]
    operations: dict[str, Pulse] = field(default_factory=_default_operations.copy)
    time_of_flight: int = field(default=180)
    smearing: int = field(default=0)

    def __post_init__(self, ports: dict[str, int]) -> NoReturn:
        """ """
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
