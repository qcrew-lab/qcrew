""" """

from numbers import Number
from typing import Callable, ClassVar

import numpy as np
from qcrew.control.pulses.waveform import Waveform
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Paramable


class Pulse(Paramable):
    """ """

    _parameters: ClassVar[set[str]] = {"pulse_type", "length", "waveforms"}

    _keyset: ClassVar[tuple[str]] = ("I", "Q", "single")
    _keysets: ClassVar[tuple[tuple[str, ...]]] = (("I", "Q"), ("single"))

    def __init__(
        self, length: int = None, **waveforms: tuple[str, Number, ...]
    ) -> None:
        """ """
        logger.info(f"Creating {type(self).__name__}...")
        self._length: int = length
        self._waveforms: dict[str, Waveform] = dict()  # updated by setter
        if waveforms:
            self.waveforms = waveforms

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}[len: {self.length}, {self.waveforms}]"

    @property  # pulse type getter
    def pulse_type(self) -> str:
        """ """
        return "control"

    @property  # pulse length getter
    def length(self) -> int:
        """ """
        has_mix_wfs, has_const_wfs = self.has_mix_waveforms, self.has_constant_waveforms
        if has_mix_wfs and not has_const_wfs:
            i_wf_len = len(self._waveforms["I"].samples)
            q_wf_len = len(self._waveforms["Q"].samples)
            if i_wf_len != q_wf_len:  # must be equal for pulse to be valid
                logger.error(f"Waveforms have unequal lengths {i_wf_len}, {q_wf_len}")
            return i_wf_len
        elif has_const_wfs:
            if self._length is None:
                logger.error("Pulse length not defined")
                raise SystemExit("Failed to get pulse length, exiting...")
            return self._length
        else:
            try:
                return len(self._waveforms["single"].samples)
            except KeyError as e:
                logger.exception(f"Invalid waveform keys, must be in {self._keysets}")
                raise SystemExit("Failed to get pulse length, exiting...") from e

    @length.setter
    def length(self, new_length: int) -> None:
        """ """
        self._length = new_length

    @property  # waveforms getter
    def waveforms(self) -> dict[str, Waveform]:
        """ """
        valid_keysets = self._keysets
        keyset = (*self._waveforms,)
        if keyset not in valid_keysets:
            logger.error(f"Invalid waveform {keyset = }, {valid_keysets = }")
            raise SystemExit("Failed to get pulse waveforms, exiting...")
        else:
            return self._waveforms

    @waveforms.setter
    def waveforms(self, new_waveforms: dict[str, tuple[str, Number, ...]]) -> None:
        """ """
        try:
            valid_keys = self._keyset
            for key in valid_keys:
                if key in new_waveforms and hasattr(self, key):
                    setattr(self, key, new_waveforms["I"])
                else:
                    logger.warning(f"Ignored invalid {key = }, {valid_keys = }")
        except TypeError as e:
            logger.error(f"Expect {dict[str, tuple]}")
            raise SystemExit("Failed to set pulse waveforms, exiting...") from e

    def _get_waveform(self, key: str) -> Waveform:
        """ """
        try:
            return self._waveforms[key]
        except KeyError:
            logger.error(f"No '{key}' waveform defined for this pulse")

    def _set_waveform(self, key: str, new_waveform: tuple[str, Number, ...]) -> None:
        """ """
        if key in self._waveforms:  # update existing waveform
            waveform = self._waveforms[key]
            waveform.fn, waveform.args = new_waveform[0], new_waveform[1:]
            logger.success(f"Updated '{key}' to {waveform}")
        else:  # create new waveform
            waveform = Waveform(*new_waveform)
            self._waveforms[key] = waveform
            logger.success(f"Set '{key}' to {waveform}")

    # pylint: disable=invalid-name
    # "I" and "Q" have specific meanings that are well understood by qcrew

    @property  # I waveform getter
    def I(self) -> Waveform:
        """ """
        return self._get_waveform("I")

    @I.setter
    def I(self, new_waveform: tuple[str, Number, ...]) -> None:
        """ """
        self._set_waveform("I", new_waveform)

    @property  # Q waveform getter
    def Q(self) -> Waveform:
        """ """
        return self._get_waveform("Q")

    @Q.setter
    def Q(self, new_waveform: tuple[str, Number, ...]) -> None:
        """ """
        self._set_waveform("Q", new_waveform)

    # pylint: enable=invalid-name

    @property  # single waveform getter
    def single(self) -> Waveform:
        """ """
        return self._get_waveform("single")

    @single.setter
    def single(self, new_waveform: tuple[str, Number, ...]) -> None:
        """ """
        self._set_waveform("single", new_waveform)

    @property  # has_mix_waveforms getter
    def has_mix_waveforms(self) -> bool:
        """ """
        return set(self._waveforms) == {"I", "Q"}

    @property  # has_constant_waveforms getter
    def has_constant_waveforms(self) -> bool:
        """ """
        for waveform in self._waveforms:
            if not waveform.is_constant:
                return False
        return True


class ReadoutPulse(Pulse):
    """ """

    # iw means integration weights
    iw_type = dict[str, tuple[Callable[int, np.ndarray], Callable[int, np.ndarray]]]

    _default_iw: ClassVar[iw_type] = {  # TODO remove defaults once we are ready
        "iw1": (np.ones, np.zeros),  # iw_name: (cos_fn, sin_fn)
        "iw2": (np.zeros, np.ones),
    }

    @property  # pulse type getter
    def pulse_type(self) -> str:
        """ """
        return "measurement"

    @property  # integration weights getter
    def iw(self) -> None:
        """ """
        return self._default_iw.copy()

    @property  # integration weight names
    def iw_names(self) -> list[str]:
        return [*self._default_iw]

p = Pulse(length=400)
print(p.parameters)
