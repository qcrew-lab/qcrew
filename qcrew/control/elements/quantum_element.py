""" """

from dataclasses import asdict, dataclass, field
from typing import ClassVar

from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Paramable
from qcrew.helpers.pulsemaker import Pulse, PulseType
from qcrew.control.instruments import LabBrick
from qcrew.control.elements.iqmixer import IQMixer


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
    single: int = field(default=None)
    # OPX AI port that the output of this QuantumElement is fed to
    out: int = field(default=None)

    # pylint: enable=invalid-name

    @property  # has_mix_inputs getter
    def has_mix_inputs(self) -> bool:
        """ """
        return self.I is not None and self.Q is not None


class QuantumElement(Paramable):
    """ """

    # class variable defining the parameter set for QuantumElement objects
    _parameters: ClassVar[set] = set()  # subclasses to override

    # class variable defining the valid keysets of the ports of QuantumElement objects
    _ports_keysets: ClassVar[set[frozenset[str]]] = set()  # subclasses to override

    # class variable defining the default operations dict for QuantumElement objects
    _default_ops: ClassVar[dict[str, PulseType]] = dict()  # subclasses to populate

    def __init__(
        self,
        name: str,
        lo: LabBrick,
        int_freq: float,
        ports: dict[str, int],
        mixer: IQMixer = None,
        operations: dict[str, PulseType] = None,
    ) -> None:
        """ """
        self._cls = type(self).__name__  # subclass name
        self._name: str = str(name)  # only gettable, not settable
        logger.info(f"Creating {self}...")

        self.lo: LabBrick = lo  # only frequency and power gettable and settable
        self.int_freq: float = int_freq  # settable

        self._ports: QuantumElementPorts = None  # set once, then only gettable
        self._create_ports(ports)  # will set self._ports

        self._mixer: IQMixer = self._check_mixer(mixer)  # set once, then only gettable

        self._operations: dict[str, PulseType] = self._default_ops.copy()  # settable
        if operations is not None:
            self.operations = operations  # update default ops with user supplied ops

        logger.info(f"Created {self}, call `.parameters` to get current state")

    def __repr__(self) -> str:
        """ """
        return f"{self._cls} '{self.name}'"

    @property  # name getter
    def name(self) -> str:
        return self._name

    @property  # lo_freq getter
    def lo_freq(self) -> float:
        """ """
        try:
            return self.lo.frequency
        except AttributeError:
            logger.exception(f"Expect lo of {LabBrick}, got {type(self.lo)}")

    @lo_freq.setter
    def lo_freq(self, new_frequency: float) -> None:
        """ """
        try:
            self.lo.frequency = new_frequency
        except AttributeError:
            logger.exception(f"Expect lo of {LabBrick}, got {type(self.lo)}")

    def _create_ports(self, initial_ports: dict[str, int]) -> QuantumElementPorts:
        """ """
        valid_keysets = [set(keyset) for keyset in self._ports_keysets]
        try:  # check if initial_ports is a dict with no invalid keys
            self._ports = QuantumElementPorts(**initial_ports)
        except TypeError as e:
            logger.exception(f"Ports must be {dict[str, int]} with {valid_keysets = }")
            raise SystemExit(f"Failed to set {self._cls} ports, exiting...") from e
        else:  # check if self._ports has a valid keyset
            ports_keys = set(self.ports)
            if ports_keys not in valid_keysets:
                logger.error(f"Got {ports_keys = }, expect one of {valid_keysets = }")
                raise ValueError(f"Invalid {self._cls} ports")

    @property  # ports getter
    def ports(self) -> dict[str, int]:
        """ """
        return {k: v for (k, v) in asdict(self._ports).items() if v is not None}

    def _check_mixer(self, mixer: IQMixer) -> IQMixer:
        """ """
        if self._ports.has_mix_inputs and not isinstance(mixer, IQMixer):
            logger.warning(f"No IQMixer found for {self.name}, creating one now...")
            return IQMixer(name=self._name + ".mixer")
        else:
            return mixer

    @property  # mixer getter
    def mixer(self) -> IQMixer:
        """ """
        return self._mixer

    @property  # operations getter
    def operations(self) -> dict[str, PulseType]:
        """ """
        return {}

    @operations.setter
    def operations(self, new_ops: dict[str, PulseType]) -> None:
        """ """
        try:
            for name, pulse in new_ops.items():
                wf_keys = set(pulse.waveforms)
                if wf_keys != {"I", "Q"} and self._ports.has_mix_inputs:
                    logger.error(f"Invalid {pulse = } for {self} with mix inputs")
                    raise SystemExit("Failed to set element operations, exiting...")
                elif wf_keys != {"single"} and not self._ports.has_mix_inputs:
                    logger.error(f"Invalid {pulse = } for {self} with single input")
                    raise SystemExit("Failed to set element operations, exiting...")
                else:
                    self._operations[str(name)] = pulse
                    logger.success(f"Set {self.name} op with {name = }, {pulse = }")
        except AttributeError as e:
            logger.exception(f"Expect {dict} with valid pulses {Pulse} as values")
            raise SystemExit("Failed to set element operations, exiting...") from e

    @operations.deleter
    def operations(self) -> None:
        """ """
        self._operations = self._default_ops.copy()
