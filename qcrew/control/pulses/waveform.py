""" """

from numbers import Number
from typing import ClassVar

from qcrew.analyze.funclib import constant_fn, gaussian_fn
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Paramable

func_map = {"constant": constant_fn, "gaussian": gaussian_fn}

class Waveform(Paramable):
    """ """

    # class variable defining the parameter set for Pulse objects
    _parameters: ClassVar[set[str]] = set(["fn", "args"])

    def __init__(self, fn: str, args: tuple[Number]) -> None:
        """ """
        self._fn: str = str(fn)  # the key in func_map of the waveform's function
        self._args: tuple[Number] = args  # arguments passed to the waveform's function

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}[{self._fn}, {self._args}]"

    @property  # fn name getter
    def fn(self) -> str:
        """ """
        return self._fn

    @property  # args getter
    def args(self) -> tuple[Number]:
        """ """
        return self._args

    @property  # samples getter
    def samples(self) -> Union[Number, np.ndarray]:
        """ """
        try:
            return func_map[self.fn](*self.args)
        except KeyError as ke:
            logger.exception(f"Unrecognized function '{self.fn}'")
            raise SystemExit("Failed to get waveform samples, exiting...") from ke
        except TypeError as te:
            logger.exception(f"Invalid arguments = {self.args} passed to {self.fn} fn")
            raise SystemExit("Failed to get waveform samples, exiting...") from te
