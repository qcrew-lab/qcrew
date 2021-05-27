""" """

from numbers import Number
from types import MappingProxyType
from typing import Callable, ClassVar, Union

import numpy as np
from qcrew.analysis.funclib import constant_fn, gaussian_fn
from qcrew.helpers import logger
from qcrew.helpers.yamlizer import Yamlable

func_map = {"constant": constant_fn, "gaussian": gaussian_fn}


class Waveform(Yamlable):
    """ """

    def __init__(self, fn: str, args: tuple[Number]) -> None:
        """ """
        self._fn: str = str(fn)  # the key in func_map of the waveform's function
        self._args: tuple[Number] = args  # arguments passed to the waveform's function

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}[{self._fn}, {self._args}]"

    def __eq__(self, other: object):
        """ """
        if isinstance(other, Waveform):
            return self._fn == other.fn and self._args == other.args
        return False

    @property  # fn name getter
    def fn(self) -> str:
        """ """
        return self._fn

    @property  # args getter
    def args(self) -> tuple[Number]:
        """ """
        return self._args

    @property  # is_constant getter
    def is_constant(self) -> bool:
        """ """
        return self._fn == "constant"

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


class ControlPulse(Yamlable):
    """ """

    # class variable defining the valid keysets of the waveforms of ControlPulse objects
    _wfs_keysets: ClassVar[set[frozenset[str]]] = set(
        [
            frozenset(["single"]),
            frozenset(["I", "Q"]),
            frozenset(["I"]),
            frozenset(["Q"]),
        ]
    )

    def __init__(self, length: int, waveforms: dict[str, Waveform]) -> None:
        """ """
        self._cls_name = type(self).__name__
        logger.info(f"Making {self._cls_name} with {length = }...")
        self._length: int = length
        self._waveforms: dict[str, Waveform] = dict()  # to be updated by setter
        self.waveforms = waveforms

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}[len: {self._length}, {self._waveforms}]"

    def __eq__(self, other: object):
        """ """
        if isinstance(other, ControlPulse):
            return self.length == other.length and self.waveforms == other.waveforms
        return False

    @property  # length getter
    def length(self) -> int:
        """ """
        return self._length

    @property  # waveforms getter
    def waveforms(self) -> dict[str, Waveform]:
        """ """
        return MappingProxyType(self._waveforms)

    @waveforms.setter
    def waveforms(self, new_wfs: dict[str, Waveform]) -> None:
        """ """
        valid_keysets = [set(keyset) for keyset in self._wfs_keysets]
        try:
            if set(new_wfs) in valid_keysets:
                for key, waveform in new_wfs.items():
                    if not isinstance(waveform, Waveform):
                        logger.warning(f"Invalid {waveform = }, must be of {Waveform}")
                    else:
                        self._waveforms[key] = waveform
                        logger.success(f"Set {self._cls_name} '{key}' {waveform = }")
            else:
                logger.warning(f"Invalid keys found, must be one of {valid_keysets = }")
        except (TypeError, AttributeError):
            logger.exception(f"Expect {dict[str, Waveform]} with {valid_keysets = }")


class MeasurementPulse(ControlPulse):
    """ """

    iw_type = dict[str, tuple[Callable[int, np.ndarray], Callable[int, np.ndarray]]]

    # class variable defining default integration weights for MeasurementPulse objects
    default_iw: ClassVar[iw_type] = {
        "iw1": (np.ones, np.zeros),  # iw_name: (cos_fn, sin_fn)
        "iw2": (np.zeros, np.ones),
    }

    def __init__(self, iw: iw_type = default_iw.copy(), **kwargs) -> None:
        """ """
        self.iw: MeasurementPulse.iw_type = iw
        super().__init__(**kwargs)

    def __eq__(self, other: object):
        """ """
        if isinstance(other, MeasurementPulse):
            return self.length == other.length and self.waveforms == other.waveforms
        return False


Pulse = (ControlPulse, MeasurementPulse)  # for isinstance checks
PulseType = Union[ControlPulse, MeasurementPulse]  # for typing hints


# ------------------------ Archetypical waveforms and pulses ---------------------------

logger.disable(__name__)  # do not log creation of these waveforms and pulses

ZERO_WAVEFORM = Waveform(fn="constant", args=(0.0,))

DEFAULT_CW_PULSE = ControlPulse(
    length=1000,
    waveforms={"I": Waveform(fn="constant", args=(0.25,)), "Q": ZERO_WAVEFORM},
)

DEFAULT_GAUSSIAN_PULSE = ControlPulse(
    length=60,
    waveforms={"I": Waveform(fn="gaussian", args=(0.25, 15, 4)), "Q": ZERO_WAVEFORM},
)

DEFAULT_READOUT_PULSE = MeasurementPulse(
    length=400,
    waveforms={"I": Waveform(fn="constant", args=(0.32,)), "Q": ZERO_WAVEFORM},
)

logger.enable(__name__)  # resume logging
