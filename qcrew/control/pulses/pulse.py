""" """

from numbers import Real
from typing import ClassVar

import numpy as np
from qcrew.control.instruments.quantum_machines import BASE_AMP, CLOCK_CYCLE
from qcrew.helpers import logger
from qcrew.helpers.parametrizer import Parametrized
from qcrew.helpers.yamlizer import Yamlable


class Pulse(Parametrized, Yamlable):
    """ """

    _parameters: ClassVar[set[str]] = {"length", "ampx"}

    def __init__(
        self,
        *,  # enforce keyword-only arguments
        length: int,
        ampx: float = 1.0,
        integration_weights=None,
    ) -> None:
        """ """
        self._length: int = length
        self.ampx: float = ampx
        self.is_readout_pulse: bool = False
        self.integration_weights = None

        if integration_weights is not None:
            self.integration_weights = integration_weights
            self.is_readout_pulse = True

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
                if name == "_length" and self.is_readout_pulse:  # set constant iw len
                    new_iw_len = int(self._length / CLOCK_CYCLE)
                    logger.info(f"Setting integration weights length = {new_iw_len}...")
                    self.integration_weights(ampx=1 / BASE_AMP, length=new_iw_len)
            elif not is_attribute:
                cls_name = type(self).__name__
                logger.warning(f"Parameter '{name}' must be an attribute of {cls_name}")
        logger.success(f"Set {self}")

    @property  # pulse length getter
    def length(self) -> int:
        """ """
        return self._length

    @property  # waveform amplitude samples getter
    def samples(self) -> tuple[np.ndarray]:
        """ """
        logger.error("Abstract method must be implemented by subclass(es)")
        raise NotImplementedError("Can't call `samples` on Pulse instance")

    # NOTE TODO this is hard coded to return constant integration weights !!!
    @property  # integration weights samples getter
    def integration_weights_samples(self) -> dict[str, dict[str, np.ndarray]]:
        """ """
        if self.integration_weights is not None:
            samples = self.integration_weights.samples
            return {
                "iwI": {
                    "cosine": samples[0],
                    "sine": samples[1],
                },
                "iwQ": {
                    "cosine": samples[1],
                    "sine": samples[0],
                },
            }
        else:
            logger.warning(f"No integration weights defined for {self}")

    @property  # pulse type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "measurement" if self.is_readout_pulse else "control"
