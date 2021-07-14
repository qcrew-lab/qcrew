""" """

from typing import Any, ClassVar

from qm import qua

from qcrew.control.instruments.vaunix.labbrick import LabBrick
from qcrew.control.pulses.constant_pulse import ConstantPulse
from qcrew.control.pulses.gaussian_pulse import GaussianPulse
from qcrew.control.pulses.pulse import Pulse
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized


class Mode(Parametrized):
    """ """

    _parameters: ClassVar[set[str]] = {
        "lo_freq",  # local oscillator frequency driving the Mode
        "int_freq",  # intermediate frequency driving the Mode
        "ports",  # OPX ports connected to this Mode
        "mixer_offsets",  # offsets used to tune the Mode's IQ mixer
        "operations",  # dict[str, Pulse] of operations that can be played to the Mode
    }
    _ports_keys: ClassVar[tuple[str]] = ("I", "Q")
    _offsets_keys: ClassVar[tuple[str]] = ("I", "Q", "G", "P")

    def __init__(
        self,
        *,  # enforce keyword-only arguments
        name: str,
        lo: LabBrick,
        int_freq: float,
        ports: dict[str, int],
        mixer_offsets: dict[str, float] = None,
        operations: dict[str, Pulse] = None,
    ) -> None:
        """ """
        self._name: str = str(name)  # name is gettable only

        self._lo: LabBrick = lo  # type check done by `lo_freq` property
        self._int_freq: float = int_freq

        self._ports: dict[str, int] = {key: None for key in self._ports_keys}
        self.ports = ports

        self._mixer_offsets: dict[str, float] = {key: 0.0 for key in self._offsets_keys}
        if mixer_offsets is not None:
            self.mixer_offsets = mixer_offsets

        self._operations: dict[str, Pulse] = dict()
        if operations is not None:  # if user specifies operations, set them
            self.operations = operations
        else:
            self.operations = {  # else set default "unselective" operations
                "constant_pulse": ConstantPulse(length=1000),
                "gaussian_pulse": GaussianPulse(sigma=100),
            }

        logger.info(f"Created {self}")

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__} '{self.name}'"

    @property  # name getter
    def name(self) -> str:
        """ """
        return self._name

    @property  # lo instrument object getter
    def lo(self) -> LabBrick:
        """ """
        return self._lo

    @property  # lo frequency getter
    def lo_freq(self) -> float:
        """ """
        try:
            return self._lo.frequency
        except AttributeError as e:
            logger.exception(f"Expect {self} lo of {LabBrick}")
            raise SystemExit("Failed to get lo frequency, exiting...") from e

    @lo_freq.setter
    def lo_freq(self, new_lo_freq: float) -> None:
        """ """
        try:
            self._lo.frequency = new_lo_freq
        except AttributeError as e:
            logger.exception(f"Expect {self} lo of {LabBrick}")
            raise SystemExit("Failed to set lo frequency, exiting...") from e

    @property  # int_freq getter
    def int_freq(self) -> float:
        """ """
        return self._int_freq

    @int_freq.setter
    def int_freq(self, new_int_freq: float) -> None:
        """ """
        self._int_freq = new_int_freq
        logger.success(f"Set {self} intermediate frequency to {new_int_freq:E}Hz")

    @property  # ports getter
    def ports(self) -> dict[str, int]:
        """ """
        return self._ports.copy()

    @ports.setter
    def ports(self, new_ports: dict[str, int]) -> None:
        """ """
        valid_keys = self._ports_keys
        try:
            for key, port in new_ports.items():
                if key in valid_keys:
                    self._ports[key] = port
                    logger.success(f"Set {self} '{key}' {port = }")
                else:
                    logger.warning(f"Invalid key '{key}', {valid_keys = }")
        except (AttributeError, TypeError) as e:
            logger.exception(f"Setter expects {dict[str, int]} with {valid_keys = }")
            raise SystemExit(f"Failed to set {self} ports, exiting...") from e

    @property  # mixer_offsets getter
    def mixer_offsets(self) -> dict[str, float]:
        """ """
        return self._mixer_offsets.copy()

    @mixer_offsets.setter
    def mixer_offsets(self, new_offsets: dict[str, float]) -> None:
        """ """
        valid_keys = self._offsets_keys
        try:
            for key, offset in new_offsets.items():
                if key in valid_keys:
                    self._mixer_offsets[key] = offset
                    logger.success(f"Set {self} '{key}' {offset = }")
                else:
                    logger.warning(f"Invalid key '{key}', {valid_keys = }")
        except TypeError as e:
            logger.exception(f"Setter expects {dict[str, float]} with {valid_keys = }")
            raise SystemExit(f"Failed to set {self} mixer offsets, exiting...") from e

    @property  # operations getter
    def operations(self) -> dict[str, Any]:
        """ """
        return self._operations.copy()

    @operations.setter
    def operations(self, new_operations: dict[str, Pulse]) -> None:
        """ """
        try:
            for name, pulse in new_operations.items():
                if isinstance(pulse, Pulse):
                    self._operations[name] = pulse
                    setattr(self, name, pulse)  # for easy access
                    logger.success(f"Set {self} operation '{name}'")
                else:
                    logger.warning(f"Invalid value '{pulse}', must be {Pulse}")
        except TypeError as e:
            logger.exception(f"Setter expects {dict[str, Pulse]}")
            raise SystemExit(f"Failed to set {self} operations, exiting...") from e

    def remove_operation(self, name: str) -> None:
        """ """
        if hasattr(self, name):
            del self._operations[name]
            delattr(self, name)
            logger.success(f"Removed {self} operation '{name}'")
        else:
            logger.warning(f"Operation '{name}' does not exist for {self}")

    @property  # has_mix_inputs getter
    def has_mix_inputs(self) -> bool:
        """ """
        return self._ports["I"] is not None and self._ports["Q"] is not None

    def play(self, key: str, ampx: tuple[float] = (1.0,), **kwargs) -> None:
        """ """  # TODO
        if key not in self._operations:
            logger.error(f"No operation named {key} defined for {self}")
            raise SystemExit("Failed to play Mode operation, exiting...")

        qua.play(key * qua.amp(*ampx), self.name, **kwargs)  # TODO
