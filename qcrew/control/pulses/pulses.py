""" """

from numbers import Real
from typing import Any, ClassVar

import numpy as np
from qcrew.control.pulses.waves import (
    ConstantWave,
    ConstantIntegrationWeight,
    GaussianWave,
    GaussianDragWave,
    IntegrationWeight,
    Wave,
)
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized
from qcrew.control.instruments.quantum_machines import CLOCK_CYCLE


class Pulse(Parametrized):
    """ """

    _parameters: ClassVar[set[str]] = {"length", "I", "Q"}

    # pylint: disable=invalid-name
    # "I" and "Q" have specific meanings that are well understood by qcrew

    def __init__(self, length: int, I: Wave, Q: Wave = None) -> None:
        """ """
        self.length: int = length
        self.I: Wave = I
        self.Q: Wave = Q

    # pylint: enable=invalid-name

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}({self.length}ns, I = {self.I}, Q = {self.Q})"

    def __call__(self, *args: Real) -> None:
        """ """
        raise NotImplementedError  # subclasses must implement

    @property  # pulse type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "control"

    @property  # has_mix_waveforms getter
    def has_mix_waveforms(self) -> bool:
        """ """
        return self.I is not None and self.Q is not None

    @property  # pulse samples getter
    def samples(self) -> tuple[np.ndarray]:
        """ """
        try:
            i_samples = self.I(**self.I.parameters)
            q_samples = None if self.Q is None else self.Q(**self.Q.parameters)
        except TypeError as e:
            logger.error(f"Expect {self} waveforms to be called with their parameters")
            raise SystemExit("Failed to get pulse samples, exiting...") from e
        return i_samples, q_samples


class ReadoutPulse(Pulse):
    """ """

    _parameters: ClassVar[set[str]] = Pulse._parameters | {"integration_weights"}

    def __init__(self, **parameters) -> None:
        """ """
        super().__init__(**parameters)
        self._integration_weights: dict[str, IntegrationWeight] = dict()

    @property  # pulse type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "measurement"

    @property  # integration weights getter
    def integration_weights(self) -> dict[str, Any]:
        """ """
        return {name: iw.parameters for name, iw in self._integration_weights.items()}

    @property  # integration weights samples getter
    def integration_weights_samples(self) -> dict[str, dict[str, np.ndarray]]:
        """ """
        iw_config = dict()
        try:
            for key, iw in self._integration_weights.items():
                iw_config[key] = {"cosine": None, "sine": None}
                cos_samples, sin_samples = iw(**iw.parameters)
                iw_config[key]["cosine"] = cos_samples
                iw_config[key]["sine"] = sin_samples
        except TypeError as te:
            logger.error(f"Expect {iw} to be called with its parameters")
            raise SystemExit("Failed to get integration weights, exiting...") from te
        else:
            return iw_config

    @integration_weights.setter
    def integration_weights(self, new_iw: dict[str, IntegrationWeight]) -> None:
        """ """
        try:
            for iw_name, iw in new_iw.items():
                if isinstance(iw, IntegrationWeight):
                    self._integration_weights[iw_name] = iw
                    setattr(self, iw_name, iw)  # for easy access
                    logger.success(f"Set readout pulse {iw} named '{iw_name}'")
                else:
                    logger.warning(f"Invalid value '{iw}', must be {IntegrationWeight}")
        except TypeError as e:
            logger.error(f"Setter expects {dict[str, IntegrationWeight]}")
            raise SystemExit("Failed to set integration weights, exiting...") from e

    def remove_integration_weight(self, iw_name: str) -> None:
        """ """
        if iw_name in self._integration_weights:
            del self._integration_weights[iw_name]
            delattr(self, iw_name)
            logger.success(f"Removed integration weight '{iw_name}'")
        else:
            logger.warning(f"Integration weight '{iw_name}' does not exist")


class ConstantPulse(Pulse):
    """ """

    def __init__(self, ampx: float, length: int) -> None:
        """ """
        i_wave = ConstantWave(ampx, length)
        q_wave = ConstantWave(0.0, length)
        super().__init__(length=length, I=i_wave, Q=q_wave)

    def __call__(self, ampx: float, length: int) -> None:
        """ """
        self.length = length
        self.I.parameters = {"length": length, "ampx": ampx}
        self.Q.parameters = {"length": length}


class GaussianPulse(Pulse):
    """ """

    def __init__(
        self, ampx: float, sigma: int, chop: int = 4, drag: float = None
    ) -> None:
        """ """
        length = sigma * chop
        i_wave = GaussianWave(ampx, sigma, chop)
        if drag is None:
            q_wave = ConstantWave(0.0, length)
        else:
            q_wave = GaussianDragWave(drag, sigma, chop)
        super().__init__(length=length, I=i_wave, Q=q_wave)

    def __call__(
        self, ampx: float, sigma: int, chop: int = 4, drag: float = None
    ) -> None:
        """ """
        self.length = sigma * chop
        self.I.parameters = {"ampx": ampx, "sigma": sigma, "chop": chop}
        if drag is None:
            self.Q.parameters = {"ampx": 0.0, "length": self.length}
        elif drag is not None and isinstance(self.Q, GaussianDragWave):
            self.Q.parameters = {"drag": drag, "sigma": sigma, "chop": chop}
        else:
            self.Q = GaussianDragWave(drag, sigma, chop)


class ConstantReadoutPulse(ReadoutPulse, ConstantPulse):
    """ """

    def __init__(self, ampx: float, length: int) -> None:
        """ """
        super().__init__(ampx=ampx, length=length)

        iw_length = int(self.length / CLOCK_CYCLE)
        self.integration_weights = {  # add default integration weights
            "iw1": ConstantIntegrationWeight(cos=1.0, sin=0.0, length=iw_length),
            "iw2": ConstantIntegrationWeight(cos=0.0, sin=1.0, length=iw_length),
        }
