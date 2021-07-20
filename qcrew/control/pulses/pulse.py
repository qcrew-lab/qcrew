""" """

from numbers import Real
from typing import ClassVar

import numpy as np

from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized
from qcrew.helpers.yamlizer import Yamlizable

BASE_PULSE_AMP = 0.2  # in V
CLOCK_CYCLE = 4  # in ns


class Pulse(Parametrized, Yamlizable):
    """ """

    _parameters: ClassVar[set[str]] = {"length", "ampx"}

    def __init__(
        self,
        *,  # enforce keyword-only arguments
        length: int = 400,
        ampx: float = 1.0,
        integration_weights=None,
    ) -> None:
        """ """
        self.is_readout_pulse: bool = False
        self.integration_weights = None

        if integration_weights is not None:
            self.integration_weights = integration_weights
            self.is_readout_pulse = True

        self.length: int = None  # length and ampx will be set by __call__()
        self.ampx: float = None
        self(length=length, ampx=ampx)

        self.has_mix_waveforms: bool = True  # qcrew's default use case

    def __repr__(self) -> str:
        """ """
        return f"{type(self).__name__}[{self.type_}]{self.parameters}"

    def __call__(self, **parameters: Real) -> None:
        """ """
        for name, value in parameters.items():
            is_attribute = hasattr(self, name)
            if is_attribute and value is not None:
                setattr(self, name, value)
                if self.is_readout_pulse:
                    self._update_integration_weights(name)
            elif not is_attribute:
                cls_name = type(self).__name__
                logger.warning(f"Parameter '{name}' must be an attribute of {cls_name}")
        logger.success(f"Set {self}")

    def _update_integration_weights(self, key: str) -> None:
        """ """
        do_update = key == "length" and self.integration_weights.is_pinned
        if do_update:
            new_iw_len = int(self.length / CLOCK_CYCLE)
            self.integration_weights.length = new_iw_len
            logger.debug(f"Set integration weights len = {new_iw_len}")

    @property  # waveform amplitude samples getter
    def samples(self) -> tuple[np.ndarray]:
        """ """
        logger.error("Abstract method must be implemented by subclass(es)")
        raise NotImplementedError("Can't call `samples` on Pulse instance")

    @property  # pulse type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "measurement" if self.is_readout_pulse else "control"
