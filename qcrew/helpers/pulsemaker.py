""" """
from dataclasses import dataclass, field
from numbers import Number
from typing import Callable, ClassVar, NoReturn, Union

import numpy as np
from qcrew.analysis.funclib import constant_fn, gaussian_fn
from qcrew.helpers import logger
from qcrew.helpers.yamlizer import Yamlable

func_map = {"constant": constant_fn, "gaussian": gaussian_fn}


@dataclass
class Waveform(Yamlable):
    """ """

    # class variable defining the name suffix of Waveform objects
    _name_suffix: ClassVar[str] = "_wf"

    fn: str  # the key in func_map that corresponds to the waveform generator function
    args: tuple[Number]  # the arguments passed to the waveform generator function

    def __post_init__(self) -> NoReturn:
        """ """
        self.name = self.fn + self._name_suffix
        logger.success("Created {} named {}", self, self.name)

    @property  # samples getter
    def samples(self) -> Union[Number, list]:
        try:
            samples = func_map[self.fn](*self.args)
        except KeyError:
            logger.exception("{} does not exist in funclib", self.fn)
            raise
        except TypeError:
            logger.exception("Invalid args {} passed to {}", self.args, self.fn)
            raise
        else:
            logger.success("Got {} sample(s) of {}", len(samples), self)
            return samples

    @property  # is_constant getter
    def is_constant(self) -> bool:
        return self.fn == "constant"


@dataclass
class ControlPulse(Yamlable):
    """ """

    # class variable defining the keyset of the waveforms of ControlPulse objects
    _waveforms_keyset: ClassVar[frozenset[frozenset[str]]] = frozenset(
        [
            frozenset(["single"]),
            frozenset(["I", "Q"]),
        ]
    )

    length: int
    waveforms: dict[str, Waveform]

    def __post_init__(self) -> NoReturn:
        """ """
        try:
            self._check_waveforms()
        except (TypeError, ValueError):
            logger.exception("Failed to validate {} waveforms", type(self).__name__)
            raise
        else:
            logger.success("Created {}", self)

    def _check_waveforms(self) -> NoReturn:
        if not isinstance(self.waveforms, dict):
            raise TypeError(
                "Expect waveforms of {}, got {}".format(
                    dict[str, Waveform], type(self.waveforms)
                )
            )
        elif set(self.waveforms) not in self._waveforms_keyset:
            logger.exception(
                "Set of keys in waveforms must be equal to one of {}",
                [set(keyset) for keyset in self._waveforms_keyset],
            )
            raise ValueError("Invalid keys found in waveforms")
        else:
            for waveform in self.waveforms.values():
                if not isinstance(waveform, Waveform):
                    logger.exception(
                        "Expected values in waveforms dict of {}, got {}",
                        Waveform,
                        type(waveform),
                    )
                    raise ValueError("Invalid waveform found in waveforms")

    @property  # has_valid_waveforms getter
    def has_valid_waveforms(self) -> bool:
        try:
            self._check_waveforms()
        except (TypeError, ValueError):
            logger.error("Failed to validate {} waveforms", type(self).__name__)
            return False
        else:
            return True

    @property  # has_single_waveform getter
    def has_single_waveform(self) -> bool:
        """ """
        try:
            self._check_waveforms()
        except (TypeError, ValueError):
            logger.error("Failed to validate {} waveforms", type(self).__name__)
            raise
        else:
            return len(self.waveforms) == 1


IntegrationWeights = dict[
    str, tuple[Callable[int, np.ndarray], Callable[int, np.ndarray]]
]


@dataclass
class MeasurementPulse(ControlPulse):
    """ """

    # class variable defining default integration weights for MeasurementPulse objects
    default_iw: ClassVar[IntegrationWeights] = {
        "iw1": (np.ones, np.zeros),  # iw_name: (cos_fn, sin_fn)
        "iw2": (np.zeros, np.ones),
    }

    iw: IntegrationWeights = field(default_factory=default_iw.copy, init=False)

    @property  # integration weights names list getter
    def iw_names(self) -> list[str]:
        return [*self.iw]


Pulse = Union[ControlPulse, MeasurementPulse]

# ------------------------ Archetypical waveforms and pulses ---------------------------

ZERO_WAVEFORM = Waveform(fn="constant", args=(0.0))
DEFAULT_CONSTANT_WAVEFORM = Waveform(fn="constant", args=(0.32))
DEFAULT_GAUSSIAN_WAVEFORM = Waveform(fn="gaussian", args=(0.25, 1000, 4))

DEFAULT_CW_PULSE = ControlPulse(
    length=1000, waveforms={"I": DEFAULT_CONSTANT_WAVEFORM, "Q": ZERO_WAVEFORM}
)
DEFAULT_GAUSSIAN_PULSE = ControlPulse(
    length=len(DEFAULT_GAUSSIAN_WAVEFORM.samples),
    waveforms={"I": DEFAULT_GAUSSIAN_WAVEFORM, "Q": ZERO_WAVEFORM},
)
DEFAULT_READOUT_PULSE = MeasurementPulse(
    length=1000, waveforms={"I": DEFAULT_CONSTANT_WAVEFORM, "Q": ZERO_WAVEFORM}
)
