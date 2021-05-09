from dataclasses import dataclass
from typing import Any

from qcrew.instruments import Instrument


@dataclass
class QuantumElement(Instrument):
    """ """

    # _lo
    lo_freq: float
    # int_freq
    # ports
    # mixer - name, offsets {i, q, g, p}
    # operations


@dataclass
class QuantumDevice(Instrument):
    """ """


@dataclass
class Qubit(QuantumElement):
    """ """

    # ports override

    @property
    def parameters(self) -> dict[str, Any]:
        return {"lo_freq": self.lo_freq}


@dataclass
class ReadoutResonator(QuantumElement):
    """ """

    # ports override
