""" """

from numbers import Number
from typing import Callable, ClassVar, NoReturn, Union

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
        self.args: tuple[Number] = args  # arguments passed to the waveform's function
        logger.info(f"Created {self}")

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}[{self.fn}, {self.args}]"

    @property  # function name getter
    def fn(self) -> str:
        return self._fn

    @property  # is_constant getter
    def is_constant(self) -> bool:
        return self._fn == "constant"

    @property  # samples getter
    def samples(self) -> Union[Number, np.ndarray]:
        try:
            samples = func_map[self.fn](*self.args)
        except KeyError as ke:
            logger.exception(f"Unrecognized function '{self.fn}'")
            raise SystemExit("Failed to get waveform samples, exiting...") from ke
        except TypeError as te:
            logger.exception(f"Invalid arguments = {self.args} passed to {self.fn} fn")
            raise SystemExit("Failed to get waveform samples, exiting...") from te
        else:
            logger.success(f"Got {len(samples)} sample(s) of {self}")
            return samples


class ControlPulse(Yamlable):
    """ """

    # class variable defining the valid keysets of the waveforms of ControlPulse objects
    _wfs_keysets: ClassVar[set[frozenset[str]]] = set(
        [
            frozenset(["single"]),
            frozenset(["I", "Q"]),
        ]
    )

    def __init__(self, length: int, waveforms: dict[str, Waveform]) -> None:
        """ """
        self.length: int = length
        self._waveforms: dict[str, Waveform] = dict()  # to be updated by setter
        self.waveforms = waveforms
        logger.info(f"Created {self}")

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}[len: {self.length}, {self.waveforms}]"

    @property  # waveforms getter
    def waveforms(self) -> dict[str, Waveform]:
        """ """
        return self._waveforms

    @waveforms.setter
    def waveforms(self, new_wfs: dict[str, Waveform]) -> NoReturn:
        """ """
        valid_keysets = [set(keyset) for keyset in self._wfs_keysets]
        try:
            if set(new_wfs) in valid_keysets:
                for key, waveform in new_wfs.items():
                    if not isinstance(waveform, Waveform):
                        logger.warning(f"Invalid {waveform = }, must be of {Waveform}")
                    else:
                        self._waveforms[key] = waveform
                        logger.success(f"Set '{key}' to {waveform}")
            else:
                logger.warning(f"Invalid keys found, must be one of {valid_keysets = }")
        except (TypeError, AttributeError):
            logger.exception(f"Expect {dict[str, Waveform]} with {valid_keysets = }")

    @property  # has_single_waveform getter
    def has_single_waveform(self) -> bool:
        """ """
        return set(self._waveforms) == {"single"}


IWType = dict[str, tuple[Callable[int, np.ndarray], Callable[int, np.ndarray]]]


class MeasurementPulse(ControlPulse):
    """ """

    # class variable defining default integration weights for MeasurementPulse objects
    default_iw: ClassVar[IWType] = {
        "iw1": (np.ones, np.zeros),  # iw_name: (cos_fn, sin_fn)
        "iw2": (np.zeros, np.ones),
    }

    def __init__(self, iw: IWType = default_iw.copy(), **kwargs) -> None:
        """ """
        self.iw: IWType = iw
        super().__init__(**kwargs)

    @property  # integration weights names list getter
    def iw_names(self) -> list[str]:
        return [*self.iw]


Pulse = (ControlPulse, MeasurementPulse)  # for isinstance checks
PulseType = Union[ControlPulse, MeasurementPulse]  # for typing hints


# ------------------------ Archetypical waveforms and pulses ---------------------------

logger.disable(__name__)  # do not log creation of these waveforms and pulses

ZERO_WAVEFORM = Waveform(fn="constant", args=(0.0))
DEFAULT_CONSTANT_WAVEFORM = Waveform(fn="constant", args=(0.32))
DEFAULT_GAUSSIAN_WAVEFORM = Waveform(fn="gaussian", args=(0.25, 1000, 4))

DEFAULT_CW_PULSE = ControlPulse(
    length=1000, waveforms={"I": DEFAULT_CONSTANT_WAVEFORM, "Q": ZERO_WAVEFORM}
)
DEFAULT_GAUSSIAN_PULSE = ControlPulse(
    length=4000,
    waveforms={"I": DEFAULT_GAUSSIAN_WAVEFORM, "Q": ZERO_WAVEFORM},
)
DEFAULT_READOUT_PULSE = MeasurementPulse(
    length=1000, waveforms={"I": DEFAULT_CONSTANT_WAVEFORM, "Q": ZERO_WAVEFORM}
)

logger.enable(__name__)  # resume logging
