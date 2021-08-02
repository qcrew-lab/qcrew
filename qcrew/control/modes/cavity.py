""" """

from typing import ClassVar
from qcrew.control.modes.mode import Mode


class Cavity(Mode):
    """ """

    _parameters: ClassVar[set[str]] = Mode._parameters | {
        "omega",  # resonance frequency, in Hz
        "t1",
        "t2",
    }

    def __init__(
        self,
        *,
        omega: float = None,
        t1: float = None,
        t2: float = None,
        **parameters,
    ):
        """ """
        super().__init__(**parameters)

        self.omega: float = omega
        self.t1: float = t1
        self.t2: float = t2
