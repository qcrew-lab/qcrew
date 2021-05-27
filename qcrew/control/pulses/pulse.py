""" """

from numbers import Number
from typing import ClassVar

from qcrew.control.pulses.waveform import Waveform
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Paramable


class Pulse(Paramable):
    """ """

    # class variable defining the parameter set for Pulse objects
    _parameters: ClassVar[set[str]] = set(["pulse_type", "length" "waveforms"])

    # pylint: disable=invalid-name
    # "I" and "Q" have specific meanings that are well understood by qcrew

    def __init__(
        self,
        length: int = 400,
        *,
        I: tuple[str, Number, ...] = None,
        Q: tuple[str, Number, ...] = None,
        single: tuple[str, Number, ...] = None
    ) -> None:
        """ """
        self._length: int = length
        self._waveforms: dict[str, Waveform] = dict()

    @property  # pulse type getter
    def pulse_type(self) -> str:
        """ """
        return "control"


class ReadoutPulse(Pulse):
    """ """

    # pylint: enable=invalid-name

    @property  # pulse type getter
    def pulse_type(self) -> str:
        """ """
        return "measurement"
