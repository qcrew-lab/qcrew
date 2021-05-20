""" """
from dataclasses import asdict, dataclass, field
from typing import ClassVar, NoReturn

from qcrew.helpers import logger
from qcrew.helpers.pulsemaker import Pulse
from qcrew.instruments import LabBrick
from qcrew.instruments.instrument import Instrument
from qcrew.instruments.meta.iqmixer import IQMixer


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

    @property  # has_output getter
    def has_output(self) -> bool:
        """ """
        return self.out is not None


class QuantumElement(Instrument):
    """ """

    # class variable defining the parameter set for QuantumElement objects
    _parameters: ClassVar[set] = set()  # subclasses to override

    # class variable defining the valid keysets of the ports of QuantumElement objects
    _ports_keysets: ClassVar[set[frozenset[str]]] = set()  # subclasses to override

    # class variable defining the default operations dict for QuantumElement objects
    _default_ops: ClassVar[dict[str, Pulse]] = dict()  # subclasses to populate

    def __init__(
        self,
        name: str,
        lo: LabBrick,
        int_freq: float,
        ports: dict[str, int],
        mixer: IQMixer = None,
        ops: dict[str, Pulse] = None,
    ) -> None:
        """ """
        self._cls = type(self).__name__  # subclass name
        self._name: str = str(name)  # only gettable, not settable

        self._lo: LabBrick = lo  # only frequency and power gettable and settable
        self.int_freq: float = int_freq  # settable

        self._ports: QuantumElementPorts = None  # set once, then only gettable
        self._create_ports(ports) # will set self._ports

        self._mixer: IQMixer = self._check_mixer(mixer)  # set once, then only gettable

        self._ops: dict[str, Pulse] = self._default_ops.copy()  # settable
        if ops is not None:
            self.ops = ops  # update default ops with user supplied ops

        logger.info(f"Created {self._cls} '{name}', get current state with .parameters")

    def __repr__(self) -> str:
        """ """
        return f"{self._cls} {self.name}"

    @property  # name getter
    def name(self) -> str:
        return self._name

    @property  # lo_freq getter
    def lo_freq(self) -> float:
        """ """
        try:
            return self._lo.frequency
        except AttributeError:
            logger.exception(f"Expect lo of {LabBrick}, got {type(self._lo)}")

    @lo_freq.setter
    def lo_freq(self, new_frequency: float) -> NoReturn:
        """ """
        try:
            self._lo.frequency = new_frequency
        except AttributeError:
            logger.exception(f"Expect lo of {LabBrick}, got {type(self._lo)}")

    @property  # lo_power getter
    def lo_power(self) -> float:
        """ """
        try:
            return self._lo.power
        except AttributeError:
            logger.exception(f"Expect lo of {LabBrick}, got {type(self._lo)}")

    @lo_power.setter
    def lo_power(self, new_power: float) -> NoReturn:
        """ """
        try:
            self._lo.power = new_power
        except AttributeError:
            logger.exception(f"Expect lo of {LabBrick}, got {type(self._lo)}")

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
            return IQMixer(name="mixer_" + self.name)
        else:
            return mixer

    @property  # mixer getter
    def mixer(self) -> IQMixer:
        """ """
        return self._mixer

    @property  # operations getter
    def ops(self) -> dict[str, Pulse]:
        """ """
        return self._ops

    @ops.setter
    def ops(self, new_ops: dict[str, Pulse]) -> NoReturn:
        """ """
        try:
            for name, pulse in new_ops.items():
                if not isinstance(pulse, Pulse):
                    logger.warning(f"Ignored invalid {pulse = }, must be of {Pulse}")
                else:
                    self._ops[str(name)] = pulse
                    logger.success(f"Set {self.name} op with {name = }, {pulse = }")
        except AttributeError:
            logger.exception(f"Ops setter expects {dict[str, Pulse]}")
