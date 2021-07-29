""" """

from typing import Any, ClassVar

import qcrew.control.instruments as qci
import qcrew.control.pulses as qcp
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized
from qcrew.helpers.yamlizer import Yamlizable

from qm import qua


class Mode(Parametrized, Yamlizable):
    """ """

    _parameters: ClassVar[set[str]] = {
        "lo_freq",  # local oscillator frequency driving the Mode
        "int_freq",  # intermediate frequency driving the Mode
        "ports",  # OPX ports connected to this Mode
        "mixer_offsets",  # offsets used to tune the Mode's IQ mixer
        "operations",  # dict[str, Pulse] of operations that can be played to the Mode
    }
    _ports_keys: ClassVar[tuple[str]] = ("I", "Q")
    _mixer_offsets_keys: ClassVar[tuple[str]] = ("I", "Q", "G", "P")

    def __init__(
        self,
        *,  # enforce keyword-only arguments
        name: str,
        lo: qci.LabBrick,
        int_freq: float,
        ports: dict[str, int],
        mixer_offsets: dict[str, float] = None,
        operations: dict[str, qcp.Pulse] = None,
    ) -> None:
        """ """
        self._name: str = str(name)  # name is gettable only

        self.lo: qci.LabBrick = lo  # type check done by `lo_freq` property
        self.int_freq: float = int_freq

        self._ports: dict[str, int] = {key: None for key in self._ports_keys}
        self.ports = ports

        self._mixer_offsets: dict[str, float] = dict()
        if mixer_offsets is not None:
            self.mixer_offsets = mixer_offsets
        else:
            self._mixer_offsets = {key: 0.0 for key in self._mixer_offsets_keys}

        self._operations: dict[str, qcp.Pulse] = dict()
        if operations is not None:
            self.operations = operations
        else:  # set default "unselective" operations
            cst_pulse = qcp.ConstantPulse(length=1000)
            gau_pulse = qcp.GaussianPulse(sigma=100)
            self.operations = {"constant_pulse": cst_pulse, "gaussian_pulse": gau_pulse}

        logger.info(f"Created {self}")

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__} '{self.name}'"

    def __setattr__(self, name: str, value: Any) -> None:
        """ """
        if hasattr(self, "_operations") and name in self._operations:
            logger.error(f"Use `.operations` to set pulses to {self}")
            raise AttributeError(f"Can't set {name} directly")
        return super().__setattr__(name, value)

    @property  # name getter
    def name(self) -> str:
        """ """
        return self._name

    @property  # lo frequency getter
    def lo_freq(self) -> float:
        """ """
        try:
            return self.lo.frequency
        except AttributeError:
            logger.error(f"Failed to get lo freq, expect {self} lo of {qci.LabBrick}")
            raise

    @lo_freq.setter
    def lo_freq(self, new_lo_freq: float) -> None:
        """ """
        try:
            self.lo.frequency = new_lo_freq
        except AttributeError:
            logger.error(f"Failed to set lo freq, expect {self} lo of {qci.LabBrick}")
            raise

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
                    logger.warning(f"Ignored invalid key '{key}', {valid_keys = }")
        except (AttributeError, TypeError):
            logger.error(f"Setter expects {dict[str, int]} with {valid_keys = }")
            raise

    @property  # mixer_offsets getter
    def mixer_offsets(self) -> dict[str, float]:
        """ """
        return self._mixer_offsets.copy()

    @mixer_offsets.setter
    def mixer_offsets(self, new_offsets: dict[str, float]) -> None:
        """ """
        valid_keys = self._mixer_offsets_keys
        try:
            for key, offset in new_offsets.items():
                if key in valid_keys:
                    self._mixer_offsets[key] = offset
                    logger.success(f"Set {self} '{key}' {offset = }")
                else:
                    logger.warning(f"Ignored invalid key '{key}', {valid_keys = }")
        except TypeError:
            logger.error(f"Setter expects {dict[str, float]} with {valid_keys = }")
            raise

    @property  # operations getter
    def operations(self) -> dict[str, Any]:
        """ """
        return self._operations.copy()

    @operations.setter
    def operations(self, new_operations: dict[str, qcp.Pulse]) -> None:
        """ """
        try:
            for name, pulse in new_operations.items():
                if isinstance(pulse, qcp.Pulse):
                    if name in self._operations:  # needed for __setattr__ override
                        del self._operations[name]
                    setattr(self, name, pulse)  # for easy access
                    self._operations[name] = pulse
                    logger.success(f"Set {self} operation '{name}'")
                else:
                    logger.warning(f"Invalid value '{pulse}', must be {qcp.Pulse}")
        except TypeError:
            logger.error(f"Setter expects {dict[str, qcp.Pulse]}")
            raise

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

    def play(self, key: str, ampx=1.0, **kwargs) -> None:
        """ """
        if key not in self._operations:
            logger.error(f"No operation named {key} defined for {self}")
            raise RuntimeError(f"Failed to play Mode operation named '{key}'")

        try:
            qua.play(key * qua.amp(ampx), self.name, **kwargs)
        except Exception:  # QM forced me to catch base class Exception...
            try:
                qua.play(key * qua.amp(*ampx), self.name, **kwargs)
            except Exception:  # QM forced me to catch base class Exception...
                logger.error("Invalid ampx, expect 1 value or sequence of 4 values")
                raise
