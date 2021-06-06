""" """

from numbers import Real
from typing import ClassVar

import numpy as np
from qcrew.control.pulses.waves import (
    ConstantWave,
    GaussianWave,
    GaussianDragWave,
    Wave,
)
from qcrew.helpers.parametrizer import Parametrized

# TODO logging, error handling, documentation


class Pulse(Parametrized):
    """ """

    _parameters: ClassVar[set[str]] = {"length", "I", "Q"}

    # pylint: disable=invalid-name
    # "I" and "Q" have specific meanings that are well understood by qcrew

    def __init__(self, length: int, I: Wave, Q: Wave = None) -> None:
        """ """
        self.length = length
        self.I = I
        self.Q = Q

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

    @property  # pulse samples getter
    def samples(self) -> tuple[np.ndarray]:
        """ """
        i_samples = self.I(**self.I.parameters)
        q_samples = None if self.Q is None else self.Q(**self.Q.parameters)
        return i_samples, q_samples


class ConstantPulse(Pulse):
    """ """

    def __init__(self, amp: float, length: int) -> None:
        """ """
        i_wave = ConstantWave(amp, length)
        q_wave = ConstantWave(0.0, length)
        super().__init__(length=length, I=i_wave, Q=q_wave)

    def __call__(self, amp: float, length: int) -> None:
        """ """
        self.length = length
        self.I.parameters = {"length": length, "amp": amp}
        self.Q.parameters = {"length": length}


class GaussianPulse(Pulse):
    """ """

    def __init__(
        self, amp: float, sigma: int, chop: int = 4, drag: float = None
    ) -> None:
        """ """
        length = sigma * chop
        i_wave = GaussianWave(amp, sigma, chop)
        if drag is None:
            q_wave = ConstantWave(0.0, length)
        else:
            q_wave = GaussianDragWave(drag, sigma, chop)
        super().__init__(length=length, I=i_wave, Q=q_wave)

    def __call__(
        self, amp: float, sigma: int, chop: int = 4, drag: float = None
    ) -> None:
        """ """
        self.length = sigma * chop
        self.I.parameters = {"amp": amp, "sigma": sigma, "chop": chop}
        if drag is None:
            self.Q.parameters = {"amp": 0.0, "length": self.length}
        elif drag is not None and isinstance(self.Q, GaussianDragWave):
            self.Q.parameters = {"drag": drag, "sigma": sigma, "chop": chop}
        else:
            self.Q = GaussianDragWave(drag, sigma, chop)


# NOTE to add a new control pulse, subclass 'Pulse', write __init__ and __call__ dunder methods to initialize and set waveform parameters respectively when called with the correct arguments.

# NOTE the code for measurement pulses is still under development...


class ConstantReadoutPulse(ConstantPulse):
    """ """

    @property  # pulse type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "measurement"

    @property  # integration weights getter
    def integration_weights(self) -> dict[str, dict[str, np.ndarray]]:
        """ """
        clock_cycles = int(self.length / 4)
        return {
            "iw1": {
                "cosine": np.ones(clock_cycles),
                "sine": np.zeros(clock_cycles),
            },
            "iw2": {
                "cosine": np.zeros(clock_cycles),
                "sine": np.ones(clock_cycles),
            },
        }


class GaussianReadoutPulse(GaussianPulse):
    """ """

    @property  # pulse type_ getter for building QM config
    def type_(self) -> str:
        """ """
        return "measurement"

    @property  # integration weights getter
    def integration_weights(self) -> None:
        """ """
        pass  # TODO
