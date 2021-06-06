""" """

from typing import ClassVar

from qcrew.control.instruments import LabBrick
from qcrew.control.pulses import (
    ConstantPulse,
    ConstantReadoutPulse,
    GaussianPulse,
    Pulse,
)
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized


class Mode(Parametrized):
    """ """

    _parameters: ClassVar[set[str]] = {
        "name",  # a string to identify the Mode in the QM config file
        "lo_freq",  # frequency of local oscillator driving the Mode
        "int_freq",  # intermediate frequency driving the Mode
        "ports",  # OPX ports connected to this Mode
        "offsets",  # offsets used to tune the Mode's IQ mixer
        "operations",  # {name: str, pulse: Pulse} Pulses that can be played to the Mode
    }
    _ports_keys: ClassVar[tuple[str]] = ("I", "Q")
    _offsets_keys: ClassVar[tuple[str]] = ("I", "Q", "G", "P")

    def __init__(
        self,
        name: str,
        lo: LabBrick,
        int_freq: float,
        ports: dict[str, int],
        offsets: dict[str, float] = None,
    ) -> None:
        """ """
        self.name: str = name
        self.lo: LabBrick = lo
        self.int_freq: float = int_freq

        self._ports: dict[str, int] = {key: None for key in self._ports_keys}
        self.ports = ports

        self._offsets: dict[str, float] = {key: None for key in self._offsets_keys}
        if offsets is not None:
            self.offsets = offsets

        self.operations: dict[str, Pulse] = {  # "unselective" operations
            "CW": ConstantPulse(amp=0.4, length=1000),
            "gaussian": GaussianPulse(amp=0.4, sigma=15, chop=4),
        }

        logger.info(f"Created {self}, call `.parameters` to get current state")

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__} '{self.name}'"

    @property  # lo_freq getter
    def lo_freq(self) -> float:
        """ """
        try:
            return self.lo.frequency
        except AttributeError as e:
            logger.exception(f"Expect lo of {LabBrick}, got {type(self.lo)}")
            raise SystemExit(f"Failed to get {self} lo frequency, exiting...") from e

    @lo_freq.setter
    def lo_freq(self, new_frequency: float) -> None:
        """ """
        try:
            self.lo.frequency = new_frequency
        except AttributeError:
            logger.exception(f"Expect lo of {LabBrick}, got {type(self.lo)}")
            raise SystemExit(f"Failed to set {self} lo frequency, exiting...") from e

    @property  # ports getter
    def ports(self) -> dict[str, int]:
        """ """
        return {key: port for key, port in self._ports.items() if port is not None}

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
                    logger.warning(f"Ignoring invalid key '{key}', {valid_keys = }")
        except TypeError as e:
            logger.exception(f"Ports must be {dict[str, int]} with {valid_keys = }")
            raise SystemExit(f"Failed to set {self} ports, exiting...") from e

    @property  # offsets getter
    def offsets(self) -> dict[str, float]:
        """ """
        return self._offsets.copy()

    @offsets.setter
    def offsets(self, new_offsets: dict[str, float]) -> None:
        """ """
        valid_keys = self._offsets_keys
        try:
            for key, offset in new_offsets.items():
                if key in valid_keys:
                    self._offsets[key] = offset
                    logger.success(f"Set {self} '{key}' {offset = }")
                else:
                    logger.warning(f"Ignoring invalid key '{key}', {valid_keys = }")
        except TypeError as e:
            logger.exception(f"Offsets must be {dict[str, float]} with {valid_keys = }")
            raise SystemExit(f"Failed to set {self} offsets, exiting...") from e


class ReadoutMode(Mode):
    """ """

    _parameters: ClassVar[set[str]] = Mode._parameters | {"time_of_flight", "smearing"}
    _ports_keys: ClassVar[tuple[str]] = (*Mode._ports_keys, "out")

    def __init__(self, time_of_flight: int, smearing: int, **parameters) -> None:
        """ """
        super().__init__(**parameters)

        self.time_of_flight: int = time_of_flight
        self.smearing: int = smearing

        self.operations.update(
            {
                "readout": ConstantReadoutPulse(amp=0.4, length=800),
            }
        )
