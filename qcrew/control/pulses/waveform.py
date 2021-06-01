""" """

from numbers import Number
from typing import ClassVar, Union

from qcrew.analyze.funclib import constant_fn, gaussian_fn
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Paramable

_FUNC_MAP = {"constant": constant_fn, "gaussian": gaussian_fn}


class Waveform(Paramable):
    """ """

    _parameters: ClassVar[set[str]] = {"fn", "args"}

    def __init__(self, fn: str, *args: Number) -> None:
        """ """
        self.fn: str = str(fn)  # key in func_map of the waveform's fn
        self.args: tuple[Number] = args  # args passed to waveform's fn

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}[{self.fn}, {self.args}]"

    @property  # is_constant getter
    def is_constant(self) -> bool:
        """ """
        return self.fn == "constant"

    @property  # samples getter
    def samples(self) -> Union[Number, list]:
        """ """
        try:
            return _FUNC_MAP[self.fn](*self.args)
        except KeyError as ke:
            logger.exception(f"Unrecognized function '{self.fn}'")
            raise SystemExit("Failed to get waveform samples, exiting...") from ke
        except TypeError as te:
            logger.exception(f"Invalid args = {self.args} passed to {self.fn} fn")
            raise SystemExit("Failed to get waveform samples, exiting...") from te
